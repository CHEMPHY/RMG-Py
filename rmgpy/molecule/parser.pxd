# global imports

cimport element as elements
cimport inchi as inchiutil

# no .pxd files for these:
#from .util cimport retrieveElementCount, VALENCES, ORDERS
#from .inchi cimport AugmentedInChI, compose_aug_inchi_key, compose_aug_inchi, INCHI_PREFIX, MULT_PREFIX, U_LAYER_PREFIX

from .molecule cimport Atom, Bond, Molecule

cpdef list BACKENDS
cpdef dict INSTALLED_BACKENDS
cpdef dict INCHI_LOOKUPS
cpdef dict SMILES_LOOKUPS


#  from <identifier> functions:

cdef Molecule __fromSMILES(Molecule mol, str smilesstr, str backend)

cdef Molecule __fromInChI(Molecule mol, str inchistr, str backend)

cdef Molecule __fromSMARTS(Molecule mol, str identifier, str backend)

cdef Molecule __parse(Molecule mol, str identifier, str type_identifier, str backend)

cpdef Molecule parse_openbabel(Molecule mol, str identifier, str type_identifier)

cpdef isCorrectlyParsed(Molecule mol, str identifier)

cpdef Molecule fromInChI(Molecule mol, str inchistr, backend=*)

cpdef Molecule fromSMILES(Molecule mol, str smilesstr, str backend=*)

cpdef Molecule fromSMARTS(Molecule mol, str smartsstr, str backend=*)

cpdef Molecule fromAugmentedInChI(Molecule mol, aug_inchi)
    
cdef Molecule __lookup(Molecule mol, str identifier, str type_identifier)

