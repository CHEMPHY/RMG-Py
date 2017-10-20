from .molecule cimport Atom, Molecule
cimport element as elements
cimport inchi as inchiutil

cpdef list BACKENDS
cpdef dict INCHI_LOOKUPS
cpdef dict SMILES_LOOKUPS

cpdef dict _known_smiles_molecules
cpdef dict _known_smiles_radicals

cpdef str toInChI(Molecule mol)

cpdef str toAugmentedInChI(Molecule mol)

cpdef str toInChIKey(Molecule mol)

cpdef str toAugmentedInChIKey(Molecule mol)

cpdef str toSMARTS(Molecule mol)

cpdef str toSMILES(Molecule mol)

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

