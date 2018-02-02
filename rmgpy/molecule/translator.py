#!/usr/bin/python
# -*- coding: utf-8 -*-

################################################################################
#
#   RMG - Reaction Mechanism Generator
#
#   Copyright (c) 2002-2015 Prof. William H. Green (whgreen@mit.edu),
#   Prof. Richard H. West (r.west@neu.edu) and the RMG Team (rmg_dev@mit.edu)
#
#   Permission is hereby granted, free of charge, to any person obtaining a
#   copy of this software and associated documentation files (the 'Software'),
#   to deal in the Software without restriction, including without limitation
#   the rights to use, copy, modify, merge, publish, distribute, sublicense,
#   and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#   FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#   DEALINGS IN THE SOFTWARE.
#
################################################################################

"""
This module provides methods for translating to and from common molecule
representation formats, e.g. SMILES, InChI, SMARTS.
"""


import cython
import itertools
import logging

# Assume that rdkit is installed
from rdkit import Chem
# Test if openbabel is installed
try:
    import openbabel
except ImportError:
    BACKENDS = ['rdkit']
else:
    BACKENDS = ['openbabel', 'rdkit']

from rmgpy.exceptions import DependencyError
from .molecule import Atom, Molecule
from rmgpy.molecule.converter import toRDKitMol, fromRDKitMol, toOBMol, fromOBMol

import rmgpy.molecule.inchi as inchiutil
import rmgpy.molecule.util as util

# constants

INCHI_LOOKUPS = {
    'H': '[H]',  # RDkit was improperly handling the Hydrogen radical from InChI
    'He': '[He]',
}
SMILES_LOOKUPS = {
    '[He]':  # RDKit improperly handles helium and returns it in a triplet state
        """
        He
        multiplicity 1
        1 He u0 p1
        """,
    '[Ar]':  # RDKit improperly handles argon
        """
        Ar
        multiplicity 1
        1 Ar u0 p4
        """,
    '[C]':  # We'd return the quintuplet without this
        """
        multiplicity 3
        1 C u2 p1 c0
        """,
    '[CH]':  # We'd return the quartet without this
        """
        multiplicity 2
        1 C u1 p1 c0 {2,S}
        2 H u0 p0 c0 {1,S}
        """,
}

#: This dictionary is used to shortcut lookups of a molecule's SMILES string from its chemical formula.
MOLECULE_LOOKUPS = {
    'N2': 'N#N',
    'CH4': 'C',
    'CH2O': 'C=O',
    'H2O': 'O',
    'C2H6': 'CC',
    'H2': '[H][H]',
    'H2O2': 'OO',
    'C3H8': 'CCC',
    'Ar': '[Ar]',
    'He': '[He]',
    'CH4O': 'CO',
    'CO2': 'O=C=O',
    'CO': '[C-]#[O+]',
    'C2H4': 'C=C',
    'O2': 'O=O',
    'C': '[C]',  # for this to be in the "molecule" list it must be singlet with 2 lone pairs
    'SO2': 'O=S=O',
    'SO3': 'O=S(=O)=O',
    'H2SO4': 'OS(=O)(=O)O',
    'N2O': 'N#[N+][O-]',
    'NH3': 'N',
    'O3': '[O-][O+]=O',
}

RADICAL_LOOKUPS = {
    'CH3': '[CH3]',
    'HO': '[OH]',
    'C2H5': 'C[CH2]',
    'O': '[O]',
    'HO2': '[O]O',
    'CH': '[CH]',
    'H': '[H]',
    'C': '[C]',  # this, in the radical list, could be triplet or quintet.
    # 'CO2': it could be [O][C][O] or O=[C][O]
    # 'CO': '[C]=O', could also be [C][O]
    # 'C2H4': could  be [CH3][CH] or [CH2][CH2]
    'O2': '[O][O]',
    'S2': '[S][S]',
    'SO': '[S][O]',
    'HSO3': 'OS(=O)[O]',
    'NO': '[N]=O',
    'NO2': 'N(=O)[O]',
}


def toInChI(mol, backend='try-all', aug_level=0):
    """
    Convert a molecular structure to an InChI string.
    For aug_level=0, generates the canonical InChI.
    For aug_level=1, appends the molecule multiplicity.
    For aug_level=2, appends positions of unpaired and paired electrons.

    Uses RDKit or OpenBabel for conversion.

    Args:
        backend     choice of backend, 'try-all', 'rdkit', or 'openbabel'
        aug_level   level of augmentation, 0, 1, or 2
    """
    cython.declare(inchi=str, ulayer=str, player=str, mlayer=str)

    if aug_level == 0:
        return _write(mol, 'inchi', backend)

    elif aug_level == 1:
        inchi = toInChI(mol, backend=backend)

        mlayer = '/mult{0}'.format(mol.multiplicity) if mol.multiplicity != 0 else ''

        return inchi + mlayer

    elif aug_level == 2:
        inchi = toInChI(mol, backend=backend)

        ulayer, player = inchiutil.create_augmented_layers(mol)

        return inchiutil.compose_aug_inchi(inchi, ulayer, player)

    else:
        raise ValueError("Implemented values for aug_level are 0, 1, or 2.")


def toInChIKey(mol, backend='try-all', aug_level=0):
    """
    Convert a molecular structure to an InChI Key string.
    For aug_level=0, generates the canonical InChI.
    For aug_level=1, appends the molecule multiplicity.
    For aug_level=2, appends positions of unpaired and paired electrons.

    Uses RDKit or OpenBabel for conversion.

    Args:
        backend     choice of backend, 'try-all', 'rdkit', or 'openbabel'
        aug_level   level of augmentation, 0, 1, or 2
    """
    cython.declare(key=str, ulayer=str, player=str, mlayer=str)

    if aug_level == 0:
        return _write(mol, 'inchikey', backend)

    elif aug_level == 1:
        key = toInChIKey(mol, backend=backend)

        mlayer = '-mult{0}'.format(mol.multiplicity) if mol.multiplicity != 0 else ''

        return key + mlayer

    elif aug_level == 2:
        key = toInChIKey(mol, backend=backend)

        ulayer, player = inchiutil.create_augmented_layers(mol)

        return inchiutil.compose_aug_inchi_key(key, ulayer, player)

    else:
        raise ValueError("Implemented values for aug_level are 0, 1, or 2.")


def toSMARTS(mol, backend='rdkit'):
    """
    Convert a molecular structure to an SMARTS string. Uses
    `RDKit <http://rdkit.org/>`_ to perform the conversion.
    Perceives aromaticity and removes Hydrogen atoms.
    """
    return _write(mol, 'sma', backend)


def toSMILES(mol, backend='default'):
    """
    Convert a molecular structure to an SMILES string.

    If there is a Nitrogen atom present it uses
    `OpenBabel <http://openbabel.org/>`_ to perform the conversion,
    and the SMILES may or may not be canonical.

    Otherwise, it uses `RDKit <http://rdkit.org/>`_ to perform the
    conversion, so it will be canonical SMILES.
    While converting to an RDMolecule it will perceive aromaticity
    and removes Hydrogen atoms.
    """
    # If we're going to have to check the formula anyway,
    # we may as well shortcut a few small known molecules.
    # Dictionary lookups are O(1) so this should be fast.
    # The dictionary is defined at the top of this file.
    try:
        if mol.isRadical():
            output = RADICAL_LOOKUPS[mol.getFormula()]
        else:
            output = MOLECULE_LOOKUPS[mol.getFormula()]
    except KeyError:
        if backend == 'default':
            for atom in mol.atoms:
                if atom.isNitrogen():
                    return _write(mol, 'smi', backend='openbabel')
            return _write(mol, 'smi', backend='rdkit')
        else:
            return _write(mol, 'smi', backend=backend)
    else:
        return output


def fromInChI(mol, inchistr, backend='try-all'):
    """
    Convert an InChI string `inchistr` to a molecular structure. Uses
    a user-specified backend for conversion, currently supporting
    rdkit (default) and openbabel.
    """
    mol.InChI = inchistr

    if inchiutil.INCHI_PREFIX in inchistr:
        return _read(mol, inchistr, 'inchi', backend)
    else:
        return _read(mol, inchiutil.INCHI_PREFIX + '/' + inchistr, 'inchi', backend)


def fromAugmentedInChI(mol, aug_inchi):
    """
    Creates a Molecule object from the augmented inchi.

    First, the inchi is converted into a Molecule using
    the backend parsers.

    Next, the multiplicity and unpaired electron information
    is used to fix a number of parsing errors made by the backends.

    Finally, the atom types of the corrected molecule are perceived.

    Returns a Molecule object
    """

    if not isinstance(aug_inchi, inchiutil.AugmentedInChI):
        aug_inchi = inchiutil.AugmentedInChI(aug_inchi)

    mol = fromInChI(mol, aug_inchi.inchi)

    mol.multiplicity = len(aug_inchi.u_indices) + 1 if aug_inchi.u_indices else 1

    inchiutil.fix_molecule(mol, aug_inchi)

    mol.updateAtomTypes()

    return mol


def fromSMARTS(mol, smartsstr, backend='rdkit'):
    """
    Convert a SMARTS string `smartsstr` to a molecular structure. Uses
    `RDKit <http://rdkit.org/>`_ to perform the conversion.
    This Kekulizes everything, removing all aromatic atom types.
    """
    return _read(mol, smartsstr, 'sma', backend)


def fromSMILES(mol, smilesstr, backend='try-all'):
    """
    Convert a SMILES string `smilesstr` to a molecular structure. Uses
    a user-specified backend for conversion, currently supporting
    rdkit (default) and openbabel.
    """
    return _read(mol, smilesstr, 'smi', backend)


def _rdkit_translator(input_object, identifier_type, mol=None):
    """
    Converts between formats using RDKit. If input is a :class:`Molecule`,
    the identifier_type is used to determine the output type. If the input is
    a `str`, then the identifier_type is used to identify the input, and the
    desired output is assumed to be a :class:`Molecule` object.

    Args:
        input_object: either molecule or string identifier
        identifier_type: format of string identifier
            'inchi'    -> InChI
            'inchikey' -> InChI Key
            'sma'      -> SMARTS
            'smi'      -> SMILES
        mol: molecule object for output (optional)
    """
    if identifier_type == 'inchi' and not Chem.inchi.INCHI_AVAILABLE:
        raise DependencyError("RDKit installed without InChI. Please reinstall to read and write InChI strings.")

    if isinstance(input_object, str):
        # We are converting from a string identifier to a molecule
        if identifier_type == 'inchi':
            rdkitmol = Chem.inchi.MolFromInchi(input_object, removeHs=False)
        elif identifier_type == 'sma':
            rdkitmol = Chem.MolFromSmarts(input_object)
        elif identifier_type == 'smi':
            rdkitmol = Chem.MolFromSmiles(input_object)
        else:
            raise ValueError('Identifier type {0} is not supported for reading using RDKit.'.format(identifier_type))
        if rdkitmol is None:
            raise ValueError("Could not interpret the identifier {0!r}".format(input_object))
        output = fromRDKitMol(mol, rdkitmol)
    elif isinstance(input_object, Molecule):
        # We are converting from a molecule to a string identifier
        rdkitmol = toRDKitMol(input_object, sanitize=False)
        if identifier_type == 'inchi':
            output = Chem.inchi.MolToInchi(rdkitmol, options='-SNon')
        elif identifier_type == 'inchikey':
            inchi = toInChI(mol)
            output = Chem.inchi.InchiToInchiKey(inchi)
        elif identifier_type == 'sma':
            output = Chem.MolToSmarts(rdkitmol)
        elif identifier_type == 'smi':
            if input_object.isAromatic():
                output = Chem.MolToSmiles(rdkitmol)
            else:
                output = Chem.MolToSmiles(rdkitmol, kekuleSmiles=True)
        else:
            raise ValueError('Identifier type {0} is not supported for writing using RDKit.'.format(identifier_type))
    else:
        raise ValueError('Unexpected input format. Should be a Molecule or a string.')

    return output


def _openbabel_translator(input_object, identifier_type, mol=None):
    """
    Converts between formats using OpenBabel. If input is a :class:`Molecule`,
    the identifier_type is used to determine the output type. If the input is
    a `str`, then the identifier_type is used to identify the input, and the
    desired output is assumed to be a :class:`Molecule` object.

    Args:
        input_object: either molecule or string identifier
        identifier_type: format of string identifier
            'inchi'    -> InChI
            'inchikey' -> InChI Key
            'smi'      -> SMILES
        mol: molecule object for output (optional)
    """
    ob_conversion = openbabel.OBConversion()

    if isinstance(input_object, str):
        # We are converting from a string identifier to a Molecule
        ob_conversion.SetInFormat(identifier_type)
        obmol = openbabel.OBMol()
        ob_conversion.ReadString(obmol, input_object)
        obmol.AddHydrogens()
        obmol.AssignSpinMultiplicity(True)
        if mol is None:
            mol = Molecule()
        output = fromOBMol(mol, obmol)
    elif isinstance(input_object, Molecule):
        # We are converting from a Molecule to a string identifier
        if identifier_type == 'inchi':
            ob_conversion.SetOutFormat('inchi')
            ob_conversion.AddOption('w')
        elif identifier_type == 'inchikey':
            ob_conversion.SetOutFormat('inchi')
            ob_conversion.AddOption('w')
            ob_conversion.AddOption('K')
        elif identifier_type == 'smi':
            ob_conversion.SetOutFormat('smi')
            # turn off isomer and stereochemistry information
            ob_conversion.AddOption('i')
        else:
            raise ValueError('Unexpected identifier type {0}.'.format(identifier_type))
        obmol = toOBMol(input_object)
        output = ob_conversion.WriteString(obmol).strip()
    else:
        raise ValueError('Unexpected input format. Should be a Molecule or a string.')

    return output


def _lookup(mol, identifier, identifier_type):
    """
    Looks up the identifier and parses it the way we think is best.

    For troublesome inchis, we look up the smiles, and parse smiles.
    For troublesome smiles, we look up the adj list, and parse the adj list.

    """
    if identifier_type.lower() == 'inchi':
        try:
            smi = INCHI_LOOKUPS[identifier.split('/', 1)[1]]
            return mol.fromSMILES(smi)
        except KeyError:
            return None
    elif identifier_type.lower() == 'smi':
        try:
            adjList = SMILES_LOOKUPS[identifier]
            return mol.fromAdjacencyList(adjList)
        except KeyError:
            return None


def _is_correctly_parsed(mol, identifier):
    """Check if molecule object has been correctly parsed."""
    conditions = []

    if mol.atoms:
        conditions.append(True)
    else:
        conditions.append(False)

    if 'InChI' in identifier:
        inchi_elementcount = util.retrieveElementCount(identifier)
        mol_elementcount = util.retrieveElementCount(mol)
        conditions.append(inchi_elementcount == mol_elementcount)

    return all(conditions)


def _read(mol, identifier, identifier_type, backend):
    """
    Parses the identifier based on the type of identifier (inchi/smi/sma)
    and the backend used.

    First, look up the identifier in a dictionary to see if it can be processed
    this way.

    If not in the dictionary, parse it through the specified backed,
    or try all backends.
    """
    # Check for potential mistakes in input arguments
    if 'InChIKey' in identifier:
        raise ValueError('InChIKey is a write-only format and cannot be parsed.')
    elif 'InChI' in identifier and identifier_type != 'inchi':
        raise ValueError('Improper identifier type "{0}". The provided identifier appears to be an InChI.'.format(identifier_type))

    if _lookup(mol, identifier, identifier_type) is not None:
        if _is_correctly_parsed(mol, identifier):
            mol.updateAtomTypes()
            return mol

    for backend in (BACKENDS if backend == 'try-all' else [backend]):
        if backend == 'rdkit':
            mol = _rdkit_translator(identifier, identifier_type, mol)
        elif backend == 'openbabel':
            mol = _openbabel_translator(identifier, identifier_type, mol)
        else:
            raise NotImplementedError("Unrecognized backend {0}".format(backend))

        if _is_correctly_parsed(mol, identifier):
            mol.updateAtomTypes()
            return mol
        else:
            logging.debug('Backend %s is not able to parse identifier %s', backend, identifier)

    raise ValueError("Unable to correctly parse {0} with backend {1}.".format(identifier, backend))


def _write(mol, identifier_type, backend):
    """
    Converts the input molecule to the specified identifier type.

    Uses backends as specified by the `backend` argument.

    Returns a string identifier of the requested type.
    """
    for backend in (BACKENDS if backend == 'try-all' else [backend]):
        if backend == 'rdkit':
            try:
                output = _rdkit_translator(mol, identifier_type)
            except ValueError:
                continue
        elif backend == 'openbabel':
            try:
                output = _openbabel_translator(mol, identifier_type)
            except ValueError:
                continue
        else:
            raise NotImplementedError("Unrecognized backend {0}".format(backend))

        return output

    raise ValueError("Unable to generate identifier type {0} with backend {1}.".format(identifier_type, backend))
