from .molecule cimport Atom, Bond, Molecule

cpdef tuple decompose(string)

cpdef str ignore_prefix(str string)

cpdef str compose_aug_inchi(str inchi, str ulayer=*, str player=*)

cpdef str compose_aug_inchi_key(str inchi_key, str ulayer=*, str player=*)

cpdef list parse_H_layer(str inchi)

cpdef list parse_E_layer(str auxinfo)

cpdef list parse_N_layer(str auxinfo)

cpdef str create_U_layer(Molecule mol, str auxinfo)

cpdef bint is_valid_combo(list combo, Molecule mol, list distances)

cpdef list find_lowest_u_layer(Molecule mol, list u_layer, list equivalent_atoms)

cpdef Molecule generate_minimum_resonance_isomer(Molecule mol)

cpdef list get_unpaired_electrons(Molecule mol)

cpdef list compute_agglomerate_distance(list agglomerates, Molecule mol)

cpdef str create_P_layer(Molecule mol, str auxinfo)

cpdef reset_lone_pairs(Molecule mol, list p_indices)

cdef Molecule fix_unsaturated_bond_to_biradical(Molecule mol, str inchi, list u_indices)

cpdef bint isUnsaturated(Molecule mol)

cpdef check(Molecule mol, aug_inchi)

cpdef fix_oxygen_unsaturated_bond(Molecule mol, list u_indices)

cpdef fixCharge(Molecule mol, list u_indices)

cpdef fix_triplet_to_singlet(Molecule mol, list p_indices)
