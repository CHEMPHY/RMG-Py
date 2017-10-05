from .molecule cimport Atom, Molecule

cpdef dict _known_smiles_molecules
cpdef dict _known_smiles_radicals

cpdef str toInChI(Molecule mol)

cpdef str toAugmentedInChI(Molecule mol)

cpdef str toInChIKey(Molecule mol)

cpdef str toAugmentedInChIKey(Molecule mol)

cpdef str toSMARTS(Molecule mol)

cpdef str toSMILES(Molecule mol)
