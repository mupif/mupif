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
# em.get_ontology("http://emmo.info/emmo/emmo-inferred#")
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
    class ThermalConductivityDimension(emmo.PhysicalDimension):
        'Thermal conductivity M¹L¹T⁻³Θ⁻¹'
        is_a=[emmo.hasSymbolData.value('T-3 L+1 M+1 Θ-1')]
    class WattPerMeterPerKelvinUnit(emmo.SICoherentDerivedUnit):
        'Thermal conductivity unit'
        emmo.altLabel=['W/m/K']
        is_a=[emmo.hasPhysicalDimension.only(ThermalConductivityDimension)]

    class PerKelvinDimension(emmo.PhysicalDimension):
        'Θ⁻¹'
        is_a=[emmo.hasSymbolData.value('Θ-1')]
    class PerKelvinUnit(emmo.SICoherentDerivedUnit):
        'Reciprocal temperature unit'
        emmo.altLabel=['K⁻¹']
        is_a=[emmo.hasPhysicalDimension.only(PerKelvinDimension)]

    class Displacement(emmo.Length): pass
    CelsiusTemperature=emmo.CelsiusTemperature
    class YoungsModulus(emmo.Stress): pass
    class ThermalConductivity(emmo.ISQDerivedQuantity):
        is_a=[
            emmo.hasReferenceUnit.only(
                WattPerMeterPerKelvinUnit # ≡ emmo.hasPhysicalDimension.only(ThermalConductivityDimension)
            ),
            emmo.hasConvention.exactly(1,emmo.Real)
        ]
    class PoissonsRatio(emmo.RatioQuantity):
        is_a=[
            emmo.hasReferenceUnit.only(emmo.LengthFractionUnit),
            emmo.hasConvention.exactly(1,emmo.Real)
        ]
    class CoeffThermalExpansion(emmo.ISQDerivedQuantity):
        is_a=[
            emmo.hasReferenceUnit.only(
                PerKelvinUnit # ≡ emmo.hasPhysicalDimension.only(PerKelvinDimension)
            ),
            emmo.hasConvention.exactly(1,emmo.Real)
        ]
    class ElasticMaterial(emmo.Material,emmo.Solid):
        """Linear elastic material with Young's modulus and Poisson's ratio."""
        is_a=[
            emmo.hasProperty.exactly(1,YoungsModulus),
            emmo.hasProperty.exactly(1,PoissonsRatio),
            emmo.hasProperty.exactly(1,CoeffThermalExpansion)
        ]
    class StationaryHeatConductionMaterial(emmo.Material,emmo.Solid):
        """Heat conduction material with thermal conductivity."""
        is_a=[emmo.hasProperty.exactly(1,ThermalConductivity)]

    class MechanicalModel(emmo.ContinuumModel):
        """2D continuum model for mechanical task."""
        is_a=[emmo.hasSpatialDirectPart.only(ElasticMaterial)]
    class stationaryThermalModel(emmo.ContinuumModel):
        """2D continuum model for thermal task."""
        is_a=[emmo.hasSpatialDirectPart.only(StationaryHeatConductionMaterial)]


tCond=ThermalConductivity()
tCond.hasForValue=1. # W/M/K
yMod=YoungsModulus()
yMod.hasForValue=30e9 # Pa
pRat=PoissonsRatio()
pRat.hasForValue=.25
cThEx=CoeffThermalExpansion()
cThEx.hasForValue=12e-6 # 1/K

eMat=ElasticMaterial()
eMat.is_a.append(emmo.hasProperty.some(yMod))
eMat.is_a.append(emmo.hasProperty.some(pRat))
eMat.is_a.append(emmo.hasProperty.some(cThEx))
cTemp=CelsiusTemperature()
cTemp.hasForValue=20.3

#onto.sync_attributes(name_policy='uuid',name_prefix='MUPIF_')

for attr in ('classes','individuals','object_properties','data_properties','annotation_properties','properties'):
    print('%s: %s\n'%(attr,str(list(getattr(onto,attr)()))))
print('units: %s'%str([c for c in onto.classes() if issubclass(c,emmo.SIUnit)]))

# this does not work really

print("Searching ontology:",onto.search(iri="*proper*"))
print("Instances of ElasticMaterial", ElasticMaterial.instances() )

if 0:
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
    #print("\nProperties", list(youngsModulus1.get_properties()))
    #print(list(YoungsModulus1.get_relations()))



