#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A script that uses EMMO to map output data to ontology in this thermo-mechanical example.
See also https://pythonhosted.org/Owlready2/
"""
import emmo as em
import owlready2
import re

owlready2.set_log_level(0)

# Load EMMO
#emmo = get_ontology() #Causes error in emmo-all-inferred
#emmo = get_ontology("http://www.emmc.info/emmc-csa/emmo-core#")
#emmo = owlready2.get_ontology("emmo-all-inferred.owl")
#emmo = owlready2.get_ontology("emmo-all-inferred.owl").load()
#emmo = get_ontology("http://test.org/onto.owl")
emmo = em.get_ontology() #overloaded method
emmo.load()
#emmo = get_ontology("http://www.emmc.info/emmo-models#")
#emmo = get_ontology("http://www.emmc.info/emmc-csa/properties")
#emmo = get_ontology("emmo-all-inferred.owl")
#emmo.load()
#print(emmo.electron_cloud)
#print(emmo.has_part)
#emmo.sync_attributes()

#emmo.sync_reasoner(reasoner="Pellet")

# Create a new ontology based on emmo
onto = owlready2.get_ontology('onto.owl')
onto.imported_ontologies.append(emmo)
onto.base_iri = 'http://www.emmc.info/emmc-csa/demo#'


# Add new classes and object/data properties needed by the use case
with onto:
    #
    # Relations, A relation is a triple (subject, property, object) where property is a Property class
    # =========
    class has_unit(emmo.has_part): #Subclass of owl.ObjectProperty, owl.TransitiveProperty, owl.ReflexiveProperty and others
        """Associates a unit to a property."""
        pass

    class is_unit_for(emmo.is_part_of):
        """Associates a property to a unit."""
        inverse_property = has_unit

    class has_type(emmo.has_convention):
        """Associates a type (string, number...) to a property."""
        pass

    class is_type_of(emmo.is_convention_for):
        """Associates a property to a type (string, number...)."""
        inverse_property = has_type

    #
    # Types
    # =====
    class integer(emmo.number):
        pass

    class real(emmo.number):
        pass

    class string(emmo.number):
        pass

    #
    # Units
    # =====
    class SI_unit(emmo.measurement_unit):
        """Base class for all SI units."""
        pass
        
    class Celsius(SI_unit):
        label = ['C']
        
    class overCelsius(SI_unit):
        label = ['1/C']
        
    class meter(SI_unit):
        label = ['m']
        
    class WoverMoverK(SI_unit):
        label = ['W/m/K']
        
    class Pascal(SI_unit):
        label = ['Pa']
        
    class Unitless(SI_unit):
        label = ['-']

    #
    # Properties
    # ==========
    #.is_a is attribute for getting the list of superclasses. The superClass may be a Class or a property restriction, for example Class.is_a.append(property.some(Value)). When defining classes, restrictions can be used in class definition. 
    #Fields in MuPIF
    class temperature(emmo.physical_quantity):
        """Temperature in degree Celsius."""
        is_a = [has_unit.exactly(1, Celsius),
                has_type.exactly(1, real)]
        
    class displacement(emmo.physical_quantity):
        """Displacement field in 2D domain."""
        is_a = [has_unit.exactly(1, meter),
                has_type.exactly(2, real)]
        
    #Properties in MuPIF
    class thermalConductivity(emmo.physical_quantity):
        """thermal conductivity."""
        is_a = [has_unit.exactly(1, WoverMoverK),
                has_type.exactly(1, real)]
        
    class YoungsModulus(emmo.physical_quantity):
        """Young's modulus."""
        is_a = [has_unit.exactly(1, Pascal),
                has_type.exactly(1, real)]

        
    class PoissonsRatio(emmo.physical_quantity):
        """Poisson's ratio."""
        is_a = [has_unit.exactly(1, Unitless),
                has_type.exactly(1, real)]
        
    class CoeffOfLinearThermalExpansion(emmo.physical_quantity):
        """Poisson's ratio."""
        is_a = [has_unit.exactly(1, overCelsius),
                has_type.exactly(1, real)]
        
        
    
    #DataProperty
    
    class has_for_value(owlready2.DataProperty, owlready2.FunctionalProperty): # FunctionalProperty - has only one number
        pass
        #range = [float]
    
    
    #ObjectProperty
    class has_for_material(owlready2.ObjectProperty):
        pass
    
 
    #
    # Material classes - continuum
    # =============================

    class elasticMaterial(emmo.material,emmo.solid):
        """Linear elastic material with Young's modulus and Poisson's ratio."""
        is_a = [emmo.has_property.exactly(1, YoungsModulus),
                emmo.has_property.exactly(1, PoissonsRatio),
                emmo.has_property.exactly(1, CoeffOfLinearThermalExpansion)]
        
    class stationaryHeatConductionMaterial(emmo.material,emmo.solid):
        """Heat conduction material with thermal conductivity."""
        is_a = [emmo.has_property.exactly(1, thermalConductivity)]

    #
    # Models
    # ======

    class mechanicalModel(emmo.continuum_model):
        """2D continuum model for mechanical task."""
        is_a = [emmo.has_spatial_direct_part.only(elasticMaterial)]
    

    class stationaryThermalModel(emmo.continuum_model):
        """2D continuum model for thermal task."""
        is_a = [emmo.has_spatial_direct_part.only(stationaryHeatConductionMaterial)]
    
    #owlready2.sync_reasoner_pellet()
    #owlready2.sync_reasoner()

#Sync attributes to make sure that all classes get a `label` and to include the docstrings in the comments
#onto.sync_attributes()

#We have defined ontology, but have to create individuals from relevant components used in computation. "Instantiate metadata".

#Define instances (named individuals)

#classes = onto.classes()
#for i in classes:
    #print(i.__name__) #get_properties()mechanicalModel

#print(mechanicalDomain.mro())
#print(temperature.is_a)

#Represent data as individuals with data properties in the ontology

thermalConductivity1 = thermalConductivity()
thermalConductivity1.has_for_value = 1.0 #in units of W/m/K

YoungsModulus1 = YoungsModulus() #stored under the name youngsModulus1
#DataType property. It is functional since individual can have this property only once.
#YoungsModulus1.has_value = 5.555 #This is not saved to owl, unfortunatelly.
YoungsModulus1.has_for_value = 30e+9 #Pa, saved to owl.

#print(list(YoungsModulus1.is_a), YoungsModulus1.is_a[0].mro(), YoungsModulus1.has_for_value, YoungsModulus1.is_a, YoungsModulus1.__class__)

PoissonsRatio1 = PoissonsRatio()
PoissonsRatio1.has_for_value = 0.25

CoeffOfLinearThermalExpansion1 = CoeffOfLinearThermalExpansion()
CoeffOfLinearThermalExpansion1.has_for_value = 12e-6 #C-1


elasticMaterial1 = elasticMaterial()
#print(elasticMaterial1)
#print(YoungsModulus1, elasticMaterial1.has_forMaterial)
elasticMaterial1.is_a.append(emmo.has_property.some(YoungsModulus1))
elasticMaterial1.is_a.append(emmo.has_property.some(PoissonsRatio1))
elasticMaterial1.is_a.append(emmo.has_property.some(CoeffOfLinearThermalExpansion1))

mechanicalModel1 = mechanicalModel()

#Easier way
mechanicalModel1.has_for_material.append(elasticMaterial1)
print(mechanicalModel1.get_properties())


#print(YoungsModulus1.__name__)
temperature1 = temperature()
temperature1.has_for_value = 20.3
#print('temperature1',temperature1.is_a, get_unit(T1))

print("\nclasses", list(onto.classes()))
print("\nindividuals", list(onto.individuals()))
print("\nobject_properties", list(onto.object_properties()))
print("\ndata_properties", list(onto.data_properties()))
print("\nannotation_properties", list(onto.annotation_properties()))
print("\nproperties", list(onto.properties()))

units = [c for c in onto.classes() if issubclass(c, onto.SI_unit)]
print("\nunits", units)
#properties = [c for c in onto.classes() if issubclass(c, onto.property) and not c in units]
#print("properties", properties)

#onto.sync_attributes(sync_imported=True)#will not work
#print('Properties', elasticMaterial1.get_properties())

#print( list(onto.individuals()) )
print("\nSearching onto", onto.search(iri = "*proper*") ) #Search ontology
print("\nInstances of class elasticMaterial", elasticMaterial.instances() )

#Run the reasoner - hermiT usually hangs, Pellet now hangs too
#owlready2.sync_reasoner_pellet(onto) 

#with onto:
    #owlready2.sync_reasoner_pellet(infer_property_values = False, infer_data_property_values = False)

#print(onto.search(has_part = "*"))

graph = owlready2.default_world.as_rdflib_graph()
#Get individuals from mechanicalModel
result = graph.query_owlready("""SELECT ?mM WHERE {?mM rdf:type <http://www.emmc.info/emmc-csa/demo#mechanicalModel> . }""")
print("\nQuery result", list(result))

#Get materials defined in mechanicalModel
result = graph.query_owlready("""SELECT ?eM WHERE { ?mM <http://www.emmc.info/emmc-csa/demo#has_for_material> ?eM  .   ?mM rdf:type <http://www.emmc.info/emmc-csa/demo#mechanicalModel> . }""")
print("\nQuery result", list(result))

#Give Young modulus of materials from mechanicalModel
result = graph.query_owlready("""SELECT ?value WHERE { ?pM <http://www.emmc.info/emmc-csa/demo#has_for_value> ?value .   ?pM <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.emmc.info/emmc-csa/demo#YoungsModulus>     .  ?bnode <http://www.w3.org/2002/07/owl#someValuesFrom> ?pM  .   ?eM <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?bnode .  ?mM <http://www.emmc.info/emmc-csa/demo#has_for_material> ?eM  .   ?mM rdf:type <http://www.emmc.info/emmc-csa/demo#mechanicalModel> . }""")
print("\nQuery result", list(result))


onto.save('usercase_ontology.owl')
onto.save('usercase_ontology.nt', format = "ntriples")

#print("Test")
#print(onto.search(subclass_of = onto.elasticMaterial))
#print(onto.search(is_a = onto.elasticMaterial))
#print(onto.search_one(label = "elasticMaterial1"))#label works only for classes, not individuals


#Caution - owlready2 does not support the access of inferred properties of individuals
#Caution - owlready searches through *.owl (or *.nt) file for triplets which are only in (no inferring)

my_world = owlready2.World()
my_world.get_ontology('usercase_ontology.owl').load()
graph = my_world.as_rdflib_graph()
#SPARQL queries in RDFlib
#r = my_world.search(entered = "*") 
#query = "SELECT ?s ?p ?o WHERE { ?s ?p ?o . }"
#query = "SELECT * WHERE { ?entity rdfs:label ?name . }"

#Find individuals of mechanicalModel
#query = "SELECT * WHERE { ?mM rdf:type <http://www.emmc.info/emmc-csa/demo#mechanicalModel> . }"

#Find materials of mechanicalModel
query = "SELECT ?eM WHERE { ?mM <http://www.emmc.info/emmc-csa/demo#has_for_material> ?eM  .   ?mM rdf:type <http://www.emmc.info/emmc-csa/demo#mechanicalModel> . }"

#Give Young modulus of materials from mechanicalModel
query = "SELECT ?value WHERE { ?pM <http://www.emmc.info/emmc-csa/demo#has_for_value> ?value .   ?pM <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.emmc.info/emmc-csa/demo#YoungsModulus>     .  ?bnode <http://www.w3.org/2002/07/owl#someValuesFrom> ?pM  .   ?eM <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?bnode .  ?mM <http://www.emmc.info/emmc-csa/demo#has_for_material> ?eM  .   ?mM rdf:type <http://www.emmc.info/emmc-csa/demo#mechanicalModel> . }"



#Find all subclasses which are inherited from 'solid'
#query = "SELECT * WHERE { ?subject rdfs:label 'solid' . }"
#query = "SELECT * WHERE { ?subject rdfs:subClassOf <http://emmc.info/emmo-material#EMMO_a2b006f2_bbfd_4dba_bcaa_3fca20cd6be1> . }"

#Find all classes of emmo.continuum_model EMMO_4456a5d2_16a6_4ee1_9a8e_5c75956b28ea (owlready2 does not support instances by inferring)
#query = "SELECT * WHERE { ?subject rdfs:subClassOf <http://emmc.info/emmo-models#EMMO_4456a5d2_16a6_4ee1_9a8e_5c75956b28ea> . }"

#Find all classes of physical_quantity
#query = "SELECT * WHERE { ?subject rdfs:subClassOf <http://emmc.info/emmo-properties#EMMO_02c0621e_a527_4790_8a0f_2bb51973c819> . }"

#Find all instances of class YoungsModulus
#query = "SELECT * WHERE { ?subject rdf:type <http://www.emmc.info/emmc-csa/demo#YoungsModulus> . }"

#Find all materials that contain an instance of youngsModulus1. We have to search across blank nodes due to multiple inheritance
#query = "SELECT ?subject WHERE { ?subject rdf:type ?bnode .   ?bnode <http://www.w3.org/2002/07/owl#someValuesFrom> <http://www.emmc.info/emmc-csa/demo#youngsModulus1> .  }"

#Give values of all youngsModulus belonging to elasticMaterial
#query = "SELECT ?prop ?value WHERE { ?prop <http://www.emmc.info/emmc-csa/demo#has_for_value> ?value .    ?bnode <http://www.w3.org/2002/07/owl#someValuesFrom> ?prop .   ?material <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?bnode . ?material <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.emmc.info/emmc-csa/demo#elasticMaterial> .  }"


#r = graph.query(query)
r = graph.query_owlready(query)
print(list(r))


#print(res[0][0])

#print('\n'.join([str(i) for i in r]))

print("\nAncestors", onto.elasticMaterial.ancestors())
print("\nSubclasses", list(onto.elasticMaterial.subclasses()))
print("\nProperties", list(YoungsModulus1.get_properties()))
#print(list(YoungsModulus1.get_relations()))



