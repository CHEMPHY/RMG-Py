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

cpdef _fix_triplet_to_singlet(Molecule mol, list p_indices)

cpdef _convert_charge_to_unpaired_electron(Molecule mol, list u_indices)

cpdef _convert_4_atom_3_bond_path(Atom start)

cpdef _convert_3_atom_2_bond_path(Atom start, Molecule mol)

cpdef _convert_delocalized_charge_to_unpaired_electron(Molecule mol, list u_indices)

cpdef _fix_adjacent_charges(Molecule mol)

cpdef _fix_charge(Molecule mol, list u_indices)

cpdef _reset_lone_pairs(Molecule mol, list p_indices)

cpdef _fix_oxygen_unsaturated_bond(Molecule mol, list u_indices)

cpdef bint _is_unsaturated(Molecule mol)

cpdef bint _convert_unsaturated_bond_to_triplet(Bond bond)

cpdef bint _fix_mobile_h(Molecule mol, str inchi, int u1, int u2)

cpdef bint _fix_butadiene_path(Atom start, Atom end)

cpdef Molecule _fix_unsaturated_bond_to_biradical(Molecule mol, str inchi, list u_indices)

cpdef _fix_unsaturated_bond(Molecule mol, list u_indices, aug_inchi)

cpdef _check_molecule(Molecule mol, aug_inchi)

cpdef fix_molecule(Molecule mol, aug_inchi)
