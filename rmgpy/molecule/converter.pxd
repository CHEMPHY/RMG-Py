from .molecule cimport Atom, Bond, Molecule


cpdef toRDKitMol(Molecule mol, bint removeHs=*, bint returnMapping=*, bint sanitize=*)

cpdef Molecule fromRDKitMol(Molecule mol, object rdkitmol)

cpdef toOBMol(Molecule mol, bint returnMapping=*)

cpdef Molecule fromOBMol(Molecule mol, object obmol)

