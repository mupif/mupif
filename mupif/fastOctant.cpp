// 2015, 2022 Václav Šmilauer <eu@doxos.eu>
// c++-based implementation of mupif.Octree.Octant
// code mostly copied over
#include<boost/multi_array.hpp>
#include<boost/core/noncopyable.hpp>
#include<pybind11/pybind11.h>
#include<pybind11/eigen.h>

//#include<boost/shared_ptr.hpp>
//#include<boost/make_shared.hpp>
#include<memory>
#include<vector>
#include<set>
#include<iostream>
#define EIGEN_NO_DEBUG
#define EIGEN_NO_ALIGN
#include<Eigen/Geometry>
using std::shared_ptr;
using std::make_shared;
using std::string;
using std::to_string;
typedef Eigen::AlignedBox<double,3> AlignedBox3d;
typedef Eigen::Matrix<double,3,1> Vector3d;
typedef Eigen::Matrix<int,3,1> Vector3i;
using Eigen::Index;
namespace py=pybind11;


/*
XDMF/hdf5 cell type codes which are supported by MuPIF and their volume is completely inside hull of their vertices. This allows an important optimization: bounding box of a cell can be computed without constructing the cell object itself, saving calls to Python from c++.
*/
std::set<int> xdmfCellType_vertexHullEnveloped={0x04,0x05,0x06,0x09,0x24};
std::map<int,int> xdmfCellType_numVertices={/*triangle*/{0x04,3},/*quad*/{0x05,4},/*tetra*/{0x06,4},/*hexa*/{0x09,8},/*quadratic triangle*/{0x24,6}};



/*
Copied from https://github.com/woodem/woo/tree/master/src/supp/eigen/pybind11
which happens to be code written by myself, so no license issues.
*/


static inline void IDX_CHECK(Eigen::Index i,Eigen::Index MAX){ if(i<0 || i>=MAX) { throw py::index_error("Index "+to_string(i)+" out of range 0.." + to_string(MAX-1)); } }
static inline void IDX2_CHECKED_TUPLE_INTS(py::tuple tuple,const Eigen::Index max2[2], Eigen::Index arr2[2]) {Eigen::Index l=py::len(tuple); if(l!=2) { PyErr_SetString(PyExc_IndexError,"Index must be integer or a 2-tuple"); throw py::error_already_set(); } for(int _i=0; _i<2; _i++) { try{ arr2[_i]=py::cast<Eigen::Index>(tuple[_i]); } catch(...){ throw py::value_error("Unable to convert "+to_string(_i)+"-th index to integer."); } IDX_CHECK(arr2[_i],max2[_i]); }  }
static inline string object_class_name(const py::object& obj){ return py::cast<string>(obj.attr("__class__").attr("__name__")); }

/* generic function to print numbers, via to_string plus padding -- used for ints */
template<typename T>
string num_to_string(const T& num, int pad=0){
	string ret(to_string(num));
	if(pad==0 || (int)ret.size()>=pad) return ret;
	return string(pad-ret.size(),' ')+ret; // left-pad with spaces
}
// for doubles, use the shortest representation
#if 0
static inline string num_to_string(const double& num, int pad=0){ return doubleToShortest(num,pad); }

/**** double-conversion helpers *****/
#include<double-conversion/double-conversion.h>

static double_conversion::DoubleToStringConverter doubleToString(
	double_conversion::DoubleToStringConverter::NO_FLAGS,
	"inf", /* infinity symbol */
	"nan", /* NaN symbol */
	'e', /*exponent symbol*/
	-5, /* decimal_in_shortest_low: 0.0001, but 0.00001->1e-5 */
	7, /* decimal_in_shortest_high */
	/* the following are irrelevant for the shortest representation */
	6, /* max_leading_padding_zeroes_in_precision_mode */
	6 /* max_trailing_padding_zeroes_in_precision_mode */
);

/* optionally pad from the left */
static inline string doubleToShortest(double d, int pad=0){
	/* 32 is perhaps wasteful */
	/* it would be better to write to the string's buffer itself, not sure how to do that */
	char buf[32];
	double_conversion::StringBuilder sb(buf,32);
	doubleToString.ToShortest(d,&sb);
	string ret(sb.Finalize());
	if(pad==0 || (int)ret.size()>=pad) return ret;
	return string(pad-ret.size(),' ')+ret; // left-padded if shorter
} 
#endif


template<typename VectorType>
static void Vector_data_stream(const VectorType& self, std::ostringstream& oss, int pad=0){
	for(Index i=0; i<self.size(); i++) oss<<(i==0?"":(((i%3)!=0 || pad>0)?",":", "))<<num_to_string(self.row(i/self.cols())[i%self.cols()],/*pad*/pad);
}

template<typename Box>
class AabbVisitor{
	typedef typename Box::VectorType VectorType;
	typedef typename Box::Scalar Scalar;
	typedef Eigen::Index Index;
	public:
	template <class PyClass>
	static void visit(PyClass& cl) {
		cl
		.def(py::init<>())
		.def(py::init(&AabbVisitor::from_tuple))
		.def(py::init(&AabbVisitor::from_list))
		.def(py::init<Box>(),py::arg("other"))
		.def(py::init<VectorType,VectorType>(),py::arg("min"),py::arg("max"))
		.def(py::pickle([](const Box& self){ return py::make_tuple(self.min(),self.max()); },&AabbVisitor::from_tuple))
		.def("volume",&Box::volume)
		.def("empty",&Box::isEmpty)
		.def("center",&Box::center)
		.def("sizes",&Box::sizes)
		.def("contains",[](const Box& self, const VectorType& pt)->bool{ return self.contains(pt);})
		.def("contains",[](const Box& self, const Box& other)->bool{ return self.contains(other);})
		// for the "in" operator
		.def("__contains__",[](const Box& self, const VectorType& pt)->bool{ return self.contains(pt);})
		.def("__contains__",[](const Box& self, const Box& other)->bool{ return self.contains(other);})
		.def("extend",[](Box& self, const VectorType& pt){ self.extend(pt);})
		.def("extend",[](Box& self, const Box& other){ self.extend(other);})
		.def("clamp",&Box::clamp)
		// return new objects
		.def("intersection",&Box::intersection)
		.def("merged",&Box::merged)
		// those return internal references, which is what we want
		// return_value_policy::reference_internal is the default for def_property
		.def_property("min",[](Box& self)->VectorType&{ return self.min(); },[](Box& self, const VectorType& v){ self.min()=v; })
		.def_property("max",[](Box& self)->VectorType&{ return self.max(); },[](Box& self, const VectorType& v){ self.max()=v; })

		.def_static("__len__",[](Box& self){ return 2; })
		.def("__setitem__",[](Box& self, py::tuple _idx, Scalar value){ Index idx[2]; Index mx[2]={2,Box::AmbientDimAtCompileTime}; IDX2_CHECKED_TUPLE_INTS(_idx,mx,idx); if(idx[0]==0) self.min()[idx[1]]=value; else self.max()[idx[1]]=value; })
		.def("__getitem__",[](const Box& self, py::tuple _idx){ Index idx[2]; Index mx[2]={2,Box::AmbientDimAtCompileTime}; IDX2_CHECKED_TUPLE_INTS(_idx,mx,idx); if(idx[0]==0) return self.min()[idx[1]]; return self.max()[idx[1]]; })
		.def("__setitem__",[](Box& self, Index idx, const VectorType& value){ IDX_CHECK(idx,2); if(idx==0) self.min()=value; else self.max()=value; })
		.def("__getitem__",[](const Box& self, Index idx){ IDX_CHECK(idx,2); if(idx==0) return self.min(); return self.max(); })
		.def("__str__",&AabbVisitor::__str__).def("__repr__",&AabbVisitor::__str__)
		;
		py::implicitly_convertible<py::tuple,Box>();
		py::implicitly_convertible<py::list,Box>();
	};
	static Box from_list(py::list l){ return from_tuple(py::tuple(l)); }
	static Box from_tuple(py::tuple t){
		if(py::len(t)!=2) throw py::type_error("Can only be constructed from a 2-tuple (not "+to_string(py::len(t))+"-tuple).");
		return Box(py::cast<VectorType>(t[0]),py::cast<VectorType>(t[1]));
	}
	static string __str__(const py::object& obj){
		const Box& self=py::cast<Box>(obj);
		std::ostringstream oss; oss<<object_class_name(obj)<<"((";
		Vector_data_stream<VectorType>(self.min(),oss);
		oss<<"), (";
		Vector_data_stream<VectorType>(self.max(),oss);
		oss<<"))";
		return oss.str();
	}
};


// arbitrary but consistent comparison function of python objects, for std::map storage
struct py_object_ptr_comparator{
	bool operator()(const py::object& a, const py::object& b) const{ return a.ptr()<b.ptr(); }
};
typedef std::set<py::object,py_object_ptr_comparator> std_set_py_object;

const size_t refineLimit=400;

AlignedBox3d bbox_mupif2eigen(py::object bb){
	try{ return py::cast<AlignedBox3d>(bb); } catch (...){};
	AlignedBox3d ret;
	if(!py::hasattr(bb,"coords_ll") || !py::hasattr(bb,"coords_ur")) throw std::runtime_error("Box (python object) does not have coords_ll and coords_ur attributes.");
	ret.min()=py::cast<Eigen::Vector3d>(bb.attr("coords_ll"));
	ret.max()=py::cast<Eigen::Vector3d>(bb.attr("coords_ur"));
	return ret;
}

#if 0
AlignedBox3d object_getBBox(const py::object& item){
	return bbox_mupif2eigen(item.attr("getBBox")());
}
#endif

struct Octant { //  XXX /* make sure copying does not happen */ public boost::noncopyable {

	struct ItemBbox{ int item; AlignedBox3d bbox; };

	AlignedBox3d box;
	//Vector3d size;
	double size;
	boost::multi_array<shared_ptr<Octant>,3> children; // initially empty
	// std::vector<py::object> data;
	std::vector<ItemBbox> data;

	/* first 2 ctor args ignored and *level*, only used for API-compatibility with Octant_py */
	Octant(/*ignored*/py::object octree,/*ignored*/py::object parent, const Vector3d& _origin, const double& _size, int level=0): box(_origin,_origin+_size*Vector3d::Ones()), size(_size) { };
	// same ctor, but without garbage args
	Octant(const Vector3d& _origin, const double& _size): box(_origin,_origin+_size*Vector3d::Ones()), size(_size) { };

	#if 0
	// pickle support
	// stuff everything into tuple, which will be passed to the ctor below
	py::tuple pickle() const {
		py::tuple childrenShape(py::make_tuple(children.shape()[0],children.shape()[1],children.shape()[2]));
		py::list childrenList;
		py::list dataList;
		for(size_t i=0; i<children.num_elements(); i++) childrenList.append(*(children.origin()+i));
		for(size_t i=0; i<data.size(); i++) dataList.append(data[i]);
		return py::make_tuple(box,size,childrenShape,childrenList,dataList);
	}
	// restore everything from that tuple, using a special ctor
	//Octant(const AlignedBox3d& _box, const double& _size, py::tuple csh, py::list childrenList, py::list dataList){
	static shared_ptr<Octant> unpickle(py::tuple dta){
		//dta: AlignedBox3d _box, double _size, py::tuple csh, py::list childrenList, py::list dataList){
		AlignedBox3d _box(py::cast<AlignedBox3d>(dta[0]));
		double _size(py::cast<double>(dta[1]));
		py::tuple csh(py::cast<py::tuple>(dta[2]));
		const int ext[3]={py::cast<int>(csh[0]),py::cast<int>(csh[1]),py::cast<int>(csh[2])};
		py::list childrenList(py::cast<py::list>(dta[3]));
		py::list dataList(py::cast<py::list>(dta[4]));
		//
		shared_ptr<Octant> ret=make_shared<Octant>(_box.min(),_size);
		// Octant ret(_box.min(),_size);
		ret->children.resize(boost::extents[ext[0]][ext[1]][ext[2]]);
		for(size_t i=0; i<py::len(childrenList); i++) *(ret->children.origin()+i)=py::cast<shared_ptr<Octant>>(childrenList[i]);
		ret->data.reserve(py::len(dataList));
		for(size_t i=0; i<py::len(dataList); i++) ret->data.push_back(dataList[i]);
		return ret;
	}
	#endif

	bool isTerminal() const{ return children.size()==0; }

	AlignedBox3d getBbox() const { return box; }
	bool containsBBox(const AlignedBox3d& b) const { return !box.intersection(b).isEmpty(); }

	void divide() {
		if(!isTerminal()) throw std::runtime_error("Attempt to divide non-terminal octant.");
		children.resize(boost::extents[2][2][2]);
		for(int i=0; i<2; i++) for(int j=0; j<2; j++) for(int k=0; k<2; k++){
			shared_ptr<Octant> oc(make_shared<Octant>(/*origin*/box.min()+.5*size*Vector3d(i,j,k),/*size*/.5*size));
			for(const ItemBbox& ib: data) oc->insert(ib);
			children[i][j][k]=oc;
		}
		// in child nodes, remove from here
		data.clear(); 
	}

	void insert_py(int item, py::object bbox){
		this->insert(ItemBbox{item,bbox_mupif2eigen(bbox)});
	}
	void insert(const ItemBbox& itemBbox){
		if(itemBbox.bbox.isEmpty()) throw std::runtime_error("item's bbox is empty.");
		// item not here, nothing to do
		if(!containsBBox(itemBbox.bbox)) return;
		// dispatch to children, finished
		if(!isTerminal()){
			for(int i=0; i<2; i++) for(int j=0; j<2; j++) for(int k=0; k<2; k++) children[i][j][k]->insert(itemBbox);
			return;
		}
		// add here
		data.push_back(itemBbox);
		// divide also copies data to new children (unlike in the python implementation)
		if(data.size()>refineLimit) divide();
	}
	void insertCellArrayChunk(const Eigen::Array<double,Eigen::Dynamic,3>& vertices, const Eigen::Array<int,Eigen::Dynamic,1>& cellData, int cellOffset){
		int numVerts=0;
		int cellNo=cellOffset;
		// std::cerr<<"Chunk: first cell is "<<cellOffset<<", chunk has "<<cellData.rows()<<" entries."<<std::endl;
		for(int icd=0; icd<cellData.rows(); icd+=numVerts+1){
			int cellType=cellData[icd];
			if(xdmfCellType_numVertices.count(cellType)==0) throw std::runtime_error("Cell "+to_string(cellNo)+": unhandled cell type "+to_string(cellType)+", cell within chunk "+to_string(icd)+", chunk offset "+to_string(cellOffset));
			numVerts=xdmfCellType_numVertices[cellType];
			if(xdmfCellType_vertexHullEnveloped.count(cellType)==0) throw std::runtime_error("Cell "+to_string(cellNo)+": cell of type "+to_string(cellType)+" is not entirely contained in hull of its vertices; this is currently unsupported for fastOctant.");
			// std::cerr<<"Cell "<<cellNo<<" ("<<icd<<" + chunk offset "<<cellOffset<<"): type "<<cellType<<", "<<numVerts<<" verts."<<std::endl;
			AlignedBox3d bb;
			for(int ic=icd+1; ic<icd+numVerts+1; ic++){
				if(ic>=cellData.rows()) throw std::runtime_error("Programming erorr: ic="+to_string(ic)+" > cellData.rows()="+to_string(cellData.rows())+")");
				// std::cerr<<"  vertex "<<cellData[ic]<<" at "<<vertices.row(cellData[ic]).matrix().eval()<<std::endl;
				bb.extend(vertices.row(cellData[ic]).matrix().transpose().eval());
			}
			this->insert(ItemBbox{cellNo,bb});
			cellNo++;
		}
	}
	#if 0
	void delete_(py::object item, AlignedBox3d itemBox=AlignedBox3d()){
		if(itemBox.isEmpty()) itemBox=object_getBBox(item);
		if(!containsBBox(itemBox)) return;
		if(!isTerminal()){
			for(int i=0; i<2; i++) for(int j=0; j<2; j++) for(int k=0; k<2; k++) children[i][j][k]->delete_(item,itemBox);
			return;
		}
		for(size_t i=0; i<data.size(); i++){ if(data[i].ptr()==item.ptr()){ data.erase(data.begin()+i); break; } }
	}
	#endif

	void getItemsInBBox_py(py::set& itemSet, const py::object& bbox_){
		getItemsInBBox(itemSet,bbox_mupif2eigen(bbox_));
	}
	void getItemsInBBox(py::set& itemSet, const AlignedBox3d& bbox){
		if(!containsBBox(bbox)) return;
		if(!isTerminal()){
			for(int i=0; i<2; i++) for(int j=0; j<2; j++) for(int k=0; k<2; k++) children[i][j][k]->getItemsInBBox(itemSet,bbox);
			return;
		}
		for(const ItemBbox& ib: data){
			if(!box.intersection(ib.bbox).isEmpty()) itemSet.add(ib.item); // PySet_Add(itemSet.ptr(),i.ptr());
		}
	}

	#if 0
	// exposed to python, checks storage type and dispatches to appropriate method
	void getItemsInBBox_dispatcher(py::object& itemStorage, py::object bbox){
		if(PySet_Check(itemStorage.ptr())){ getItemsInBBox_set(itemStorage,bbox_mupif2eigen(bbox)); return; }
		try{
			getItemsInBBox_list(py::cast<py::list>(itemStorage),bbox_mupif2eigen(bbox));
			return;
		} catch(...) { };
		throw std::runtime_error("itemStorage must be set or list.");
	}

	void getItemsInBBox_list(py::list itemList, const AlignedBox3d& bbox){
		if(!containsBBox(bbox)) return;
		if(!isTerminal()){
			for(int i=0; i<2; i++) for(int j=0; j<2; j++) for(int k=0; k<2; k++) children[i][j][k]->getItemsInBBox_list(itemList,bbox);
			return;
		}
		for(const py::object& i: data){
			if(!box.intersection(object_getBBox(i)).isEmpty()) itemList.append(i);
		}
	}
		void evaluate(py::object functor, AlignedBox3d functorBox=AlignedBox3d()){
			if(functorBox.isEmpty()) functorBox=object_getBBox(functor);
			if(!containsBBox(functorBox)) return;
			if(!isTerminal()){
				for(int i=0; i<2; i++) for(int j=0; j<2; j++) for(int k=0; k<2; k++) children[i][j][k]->evaluate(functor,functorBox);
				return;
			}
			for(const py::object& i: data){
				// if(!box.intersects(object_getBBox(i))) continue; /* needed? not in python */
				functor.attr("evaluate")(i);
			}
		}
		int giveDepth() { throw std::runtime_error("Octant.giveDepth: not impelmented in c++"); }
	#endif
};

PYBIND11_MODULE(fastOctant,mod){
	mod.doc()="c++ implementation of the Octant class, which aims at high performance but copies the Python API. It is monkey-patched into mupif at runtime, if detected, without any user intervention necessary.";

	py::class_<AlignedBox3d> cAB3d(mod,"AlignedBox3","Axis-aligned box object, defined by its minimum and maximum corners");
		AabbVisitor<AlignedBox3d>::visit(cAB3d);

	py::class_<Octant,shared_ptr<Octant>>(mod,"Octant")
		.def(py::init<const Vector3d&, const double&>(),py::arg("min"),py::arg("size"))
		.def(py::init<py::object,py::object,const Vector3d&,const double&,int>(),py::arg("octree"),py::arg("parent"),py::arg("origin"),py::arg("size"),py::arg("level")=0)
		.def("isTerminal",&Octant::isTerminal)
		.def("insert",&Octant::insert_py,py::arg("item"),py::arg("bbox"))
		.def("insertCellArrayChunk",&Octant::insertCellArrayChunk,py::arg("vertices"),py::arg("cellData"),py::arg("cellOffset"))
		.def("getItemsInBBox",&Octant::getItemsInBBox_py,py::arg("itemSet"),py::arg("bbox"))
		#if 0
			.def("getBBox",&Octant::getBBox)
			.def("evaluate",&Octant::evaluate,py::arg("functor"),py::arg("bbox")=AlignedBox3d())
			.def("getDepth",&Octant::getDepth)
			.def("delete",&Octant::delete_,py::arg("item"),py::arg("bbox")=AlignedBox3d())
			.def(py::pickle(&Octant::pickle,&Octant::unpickle))	
		#endif
	;

		/* not exposed:
			.def("containsBBox",&Octant::containsBBox)
			.def("divide",&Octant::divide)
		 */

};
