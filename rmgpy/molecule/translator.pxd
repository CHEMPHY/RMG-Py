from .molecule cimport Atom, Molecule
cimport element as elements
cimport inchi as inchiutil

cpdef list BACKENDS
cpdef dict INCHI_LOOKUPS
cpdef dict SMILES_LOOKUPS

cpdef dict MOLECULE_LOOKUPS
cpdef dict RADICAL_LOOKUPS

cpdef str toInChI(Molecule mol, backend=?)

cpdef str toAugmentedInChI(Molecule mol)

cpdef str toInChIKey(Molecule mol, backend=?)

cpdef str toAugmentedInChIKey(Molecule mol)

cpdef str toSMARTS(Molecule mol, backend=?)

cpdef str toSMILES(Molecule mol, backend=?)

cpdef Molecule fromInChI(Molecule mol, str inchistr, backend=?)

cpdef Molecule fromSMILES(Molecule mol, str smilesstr, str backend=?)

cpdef Molecule fromSMARTS(Molecule mol, str smartsstr, str backend=?)

cpdef Molecule fromAugmentedInChI(Molecule mol, aug_inchi)

cpdef object _rdkit_translator(object input_object, str identifier_type, Molecule mol=?)

cpdef object _openbabel_translator(object input_object, str identifier_type, Molecule mol=?)

cdef Molecule _lookup(Molecule mol, str identifier, str identifier_type)

cpdef _is_correctly_parsed(Molecule mol, str identifier)

cdef Molecule _read(Molecule mol, str identifier, str identifier_type, str backend)

cdef str _write(Molecule mol, str identifier_type, str backend)
