// 2015 Václav Šmilauer <eu@doxos.eu>
// c++-based implementation of mupif.Octree.Octant
// code mostly copied over
#include<boost/python.hpp>
#include<boost/multi_array.hpp>
#include<boost/shared_ptr.hpp>
#include<boost/make_shared.hpp>
#include<vector>
#include<set>
#define EIGEN_NO_DEBUG
#define EIGEN_NO_ALIGN
#include<Eigen/Geometry>
using boost::shared_ptr;
using boost::make_shared;
typedef Eigen::AlignedBox<double,3> AlignedBox3d;
typedef Eigen::Matrix<double,3,1> Vector3d;
typedef Eigen::Matrix<int,3,1> Vector3i;
namespace py=boost::python;

// arbitrary but consistent comparison function of python objects, for std::map storage
struct py_object_ptr_comparator{
	bool operator()(const py::object& a, const py::object& b) const{ return a.ptr()<b.ptr(); }
};
typedef std::set<py::object,py_object_ptr_comparator> std_set_py_object;

const size_t refineLimit=400;

AlignedBox3d object_getBBox(const py::object& item){
	py::extract<AlignedBox3d> ex(item.attr("getBBox")());
	if(!ex.check()) throw std::runtime_error("getBBox() returned a result not convertible to minieigen.AlignedBox3.");
	return ex();
}

struct Octant{
	AlignedBox3d box;
	//Vector3d size;
	double size;
	boost::multi_array<shared_ptr<Octant>,3> children; // initially empty
	std::vector<py::object> data;

	/* first 2 ctor args ignored, only for compatibility with the Python version API */
	/* if minieigen module is loaded, converters from 3-sequences to Vector3d will converts args for us */
	Octant(/*ignored*/py::object octree,/*ignored*/py::object parent, const Vector3d& _origin, const double& _size): box(_origin,_origin+_size*Vector3d::Ones()), size(_size) { };
	// same ctor, but without garbage arge
	Octant(const Vector3d& _origin, const double& _size): box(_origin,_origin+_size*Vector3d::Ones()), size(_size) { };

	bool isTerminal() const{ return children.size()==0; }

	AlignedBox3d giveMyBBox() const { return box; }
	bool containsBBox(const AlignedBox3d& b) const { return !box.intersection(b).isEmpty(); }

	void divide() {
		if(!isTerminal()) throw std::runtime_error("Attempt to divide non-terminal octant.");
		children.resize(boost::extents[2][2][2]);
		for(int i=0; i<2; i++) for(int j=0; j<2; j++) for(int k=0; k<2; k++){
			shared_ptr<Octant> oc(make_shared<Octant>(/*origin*/box.min()+.5*size*Vector3d(i,j,k),/*size*/.5*size));
			for(const py::object& i: data) oc->insert(i);
			children[i][j][k]=oc;
		}
		// in child nodes, remove from here
		data.clear(); 
	}

	void insert(const py::object& item, AlignedBox3d itemBox=AlignedBox3d()){
		if(itemBox.isEmpty()) itemBox=object_getBBox(item);
		// item not here, nothing to do
		if(!containsBBox(itemBox)) return;
		// dispatch to children, finished
		if(!isTerminal()){
			for(int i=0; i<2; i++) for(int j=0; j<2; j++) for(int k=0; k<2; k++) children[i][j][k]->insert(item,itemBox);
			return;
		}
		// add here
		data.push_back(item);
		// divide also copies data to new children (unlike in the python implementation)
		if(data.size()>refineLimit) divide();
	}

	void delete_(py::object item, AlignedBox3d itemBox=AlignedBox3d()){
		if(itemBox.isEmpty()) itemBox=object_getBBox(item);
		if(!containsBBox(itemBox)) return;
		if(!isTerminal()){
			for(int i=0; i<2; i++) for(int j=0; j<2; j++) for(int k=0; k<2; k++) children[i][j][k]->delete_(item,itemBox);
			return;
		}
		for(size_t i=0; i<data.size(); i++){ if(data[i].ptr()==item.ptr()){ data.erase(data.begin()+i); break; } }
	}


	// exposed to python, checks storage type and dispatches to appropriate method
	void giveItemsInBBox_dispatcher(py::object& itemStorage, const AlignedBox3d& bbox){
		if(PySet_Check(itemStorage.ptr())){ giveItemsInBBox_set(itemStorage,bbox); return; }
		py::extract<py::list> exList(itemStorage);
		if(exList.check()){ giveItemsInBBox_list(exList(),bbox); return; }
		throw std::runtime_error("itemStorage must be set or list.");
	}

	void giveItemsInBBox_list(py::list itemList, const AlignedBox3d& bbox){
		if(!containsBBox(bbox)) return;
		if(!isTerminal()){
			for(int i=0; i<2; i++) for(int j=0; j<2; j++) for(int k=0; k<2; k++) children[i][j][k]->giveItemsInBBox_list(itemList,bbox);
			return;
		}
		for(const py::object& i: data){
			if(!box.intersection(object_getBBox(i)).isEmpty()) itemList.append(i);
		}
	}

	void giveItemsInBBox_set(py::object& itemSet, const AlignedBox3d& bbox){
		if(!containsBBox(bbox)) return;
		if(!isTerminal()){
			for(int i=0; i<2; i++) for(int j=0; j<2; j++) for(int k=0; k<2; k++) children[i][j][k]->giveItemsInBBox_set(itemSet,bbox);
			return;
		}
		for(const py::object& i: data){
			if(!box.intersection(object_getBBox(i)).isEmpty()) PySet_Add(itemSet.ptr(),i.ptr());
		}
	}

	#if 0
	py::list giveItemsInBBox_list_unique(const AlignedBox3d& bbox){
		set_set_py_object itemSet;
		giveItemsInBBox_set_cxx(itemSet,bbox);
		py::list ret;
		for(py::object& o: itemSet)

	}


	void giveItemsInBBox_set_cxx(std_set_py_object& itemSet, const AlignedBox3d& bbox){
		if(!containsBBox(bbox)) return;
		if(!isTerminal()){
			for(int i=0; i<2; i++) for(int j=0; j<2; j++) for(int k=0; k<2; k++) children[i][j][k]->giveItemsInBBox_cxx(itemSet,bbox);
			return;
		}
		for(const py::object& i: data){
			if(!box.intersection(object_getBBox(i)).isEmpty()) itemList.insert(i);
		}
	}
	#endif

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
};

BOOST_PYTHON_MODULE(fastOctant){
	py::scope().attr("__doc__")="c++ implementation of the Octant class, which aims at high performance but copies the Python API. It is monkey-patched into mupif at runtime, if detected, without any user intervention necessary.";

	py::class_<Octant,shared_ptr<Octant>,boost::noncopyable>("Octant",py::init<const Vector3d&, const double&>())
		.def(py::init<py::object,py::object,const Vector3d&,const double&>())
		.def("isTerminal",&Octant::isTerminal)
		.def("insert",&Octant::insert,(py::arg("item"),py::arg("bbox")=AlignedBox3d()))
		.def("giveItemsInBBox",&Octant::giveItemsInBBox_dispatcher,(py::arg("itemStorage"),py::arg("bbox")))
		.def("delete",&Octant::delete_,(py::arg("item"),py::arg("bbox")=AlignedBox3d()))
		.def("evaluate",&Octant::evaluate,(py::arg("functor"),py::arg("bbox")=AlignedBox3d()))
		.def("giveDepth",&Octant::giveDepth)
		.def("giveMyBBox",&Octant::giveMyBBox)
		/* not exposed:
			.def("containsBBox",&Octant::containsBBox)
			.def("divide",&Octant::divide)
		 */
	;
};

