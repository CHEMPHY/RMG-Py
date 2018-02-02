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

from .molecule import Atom
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


def toInChI(mol):
    """
    Convert a molecular structure to an InChI string. Uses
    `RDKit <http://rdkit.org/>`_ to perform the conversion.
    Perceives aromaticity.

    or

    Convert a molecular structure to an InChI string. Uses
    `OpenBabel <http://openbabel.org/>`_ to perform the conversion.
    """
    try:
        if not Chem.inchi.INCHI_AVAILABLE:
            return "RDKitInstalledWithoutInChI"
        rdkitmol = toRDKitMol(mol)
        return Chem.inchi.MolToInchi(rdkitmol, options='-SNon')
    except:
        pass

    obmol = toOBMol(mol)
    obConversion = openbabel.OBConversion()
    obConversion.SetOutFormat('inchi')
    obConversion.SetOptions('w', openbabel.OBConversion.OUTOPTIONS)
    return obConversion.WriteString(obmol).strip()


def toAugmentedInChI(mol):
    """
    This function generates the augmented InChI canonical identifier, and that allows for the differentiation
    between structures with spin states and multiple unpaired electrons.

    Two additional layers are added to the InChI:
    - unpaired electrons layer: the position of the unpaired electrons in the molecule

    """

    cython.declare(
        inchi=str,
        ulayer=str,
        aug_inchi=str,
    )
    inchi = toInChI(mol)

    ulayer, player = inchiutil.create_augmented_layers(mol)

    aug_inchi = inchiutil.compose_aug_inchi(inchi, ulayer, player)

    return aug_inchi


def toInChIKey(mol):
    """
    Convert a molecular structure to an InChI Key string. Uses
    `OpenBabel <http://openbabel.org/>`_ to perform the conversion.

    or

    Convert a molecular structure to an InChI Key string. Uses
    `RDKit <http://rdkit.org/>`_ to perform the conversion.

    Removes check-sum dash (-) and character so that only
    the 14 + 9 characters remain.
    """
    try:
        if not Chem.inchi.INCHI_AVAILABLE:
            return "RDKitInstalledWithoutInChI"
        inchi = toInChI(mol)
        return Chem.inchi.InchiToInchiKey(inchi)[:-2]
    except:
        pass

    # for atom in mol.vertices:
    #           if atom.isNitrogen():
    obmol = toOBMol(mol)
    obConversion = openbabel.OBConversion()
    obConversion.SetOutFormat('inchi')
    obConversion.SetOptions('w', openbabel.OBConversion.OUTOPTIONS)
    obConversion.SetOptions('K', openbabel.OBConversion.OUTOPTIONS)
    return obConversion.WriteString(obmol).strip()[:-2]


def toAugmentedInChIKey(mol):
    """
    Adds additional layers to the InChIKey,
    generating the "augmented" InChIKey.
    """

    cython.declare(
        key=str,
        ulayer=str
    )

    key = toInChIKey(mol)

    ulayer, player = inchiutil.create_augmented_layers(mol)

    return inchiutil.compose_aug_inchi_key(key, ulayer, player)


def toSMARTS(mol):
    """
    Convert a molecular structure to an SMARTS string. Uses
    `RDKit <http://rdkit.org/>`_ to perform the conversion.
    Perceives aromaticity and removes Hydrogen atoms.
    """
    rdkitmol = toRDKitMol(mol)

    return Chem.MolToSmarts(rdkitmol)


def toSMILES(mol):
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
    # Dictionary lookups are O(1) so this should be fast:
    # The dictionary is defined at the top of this file.

    cython.declare(
        atom=Atom,
        # obmol=,
        # rdkitmol=,
    )

    try:
        if mol.isRadical():
            return RADICAL_LOOKUPS[mol.getFormula()]
        else:
            return MOLECULE_LOOKUPS[mol.getFormula()]
    except KeyError:
        # It wasn't in the above list.
        pass
    for atom in mol.vertices:
        if atom.isNitrogen():
            obmol = toOBMol(mol)
            try:
                SMILEwriter = openbabel.OBConversion()
                SMILEwriter.SetOutFormat('smi')
                SMILEwriter.SetOptions("i",
                                       SMILEwriter.OUTOPTIONS)  # turn off isomer and stereochemistry information (the @ signs!)
            except:
                pass
            return SMILEwriter.WriteString(obmol).strip()

    rdkitmol = toRDKitMol(mol, sanitize=False)
    if not mol.isAromatic():
        return Chem.MolToSmiles(rdkitmol, kekuleSmiles=True)
    return Chem.MolToSmiles(rdkitmol)



def __fromSMILES(mol, smilesstr, backend):
    """Replace the Molecule `mol` with that given by the SMILES `smilesstr`
       using the backend `backend`"""
    if backend.lower() == 'rdkit':
        rdkitmol = Chem.MolFromSmiles(smilesstr)
        if rdkitmol is None:
            raise ValueError("Could not interpret the SMILES string {0!r}".format(smilesstr))
        fromRDKitMol(mol, rdkitmol)
        return mol
    elif backend.lower() == 'openbabel':
        parse_openbabel(mol, smilesstr, 'smi')
        return mol
    else:
        raise NotImplementedError('Unrecognized backend for SMILES parsing: {0}'.format(backend))


def __fromInChI(mol, inchistr, backend):
    """Replace the Molecule `mol` with that given by the InChI `inchistr`
       using the backend `backend`"""
    if backend.lower() == 'rdkit':
        rdkitmol = Chem.inchi.MolFromInchi(inchistr, removeHs=False)
        mol = fromRDKitMol(mol, rdkitmol)
        return mol
    elif backend.lower() == 'openbabel':
        return parse_openbabel(mol, inchistr, 'inchi')
    else:
        raise NotImplementedError('Unrecognized backend for InChI parsing: {0}'.format(backend))


def __fromSMARTS(mol, smartsstr, backend):
    """Replace the Molecule `mol` with that given by the SMARTS `smartsstr`
       using the backend `backend`"""
    if backend.lower() == 'rdkit':
        rdkitmol = Chem.MolFromSmarts(smartsstr)
        if rdkitmol is None:
            raise ValueError("Could not interpret the SMARTS string {0!r}".format(smartsstr))
        fromRDKitMol(mol, rdkitmol)
        return mol
    else:
        raise NotImplementedError('Unrecognized backend for SMARTS parsing: {0}'.format(backend))


def __parse(mol, identifier, type_identifier, backend):
    """
    Parses the identifier based on the type of identifier (inchi/smi/sma)
    and the backend used.

    First, look up the identifier in a dictionary to see if it can be processed
    this way.

    If not in the dictionary, parse it through the specified backed,
    or try all backends.

    """

    if __lookup(mol, identifier, type_identifier) is not None:
        if isCorrectlyParsed(mol, identifier):
            mol.updateAtomTypes()
            return mol

    for _backend in (BACKENDS if backend == 'try-all' else [backend]):
        if type_identifier == 'smi':
            __fromSMILES(mol, identifier, _backend)
        elif type_identifier == 'inchi':
            __fromInChI(mol, identifier, _backend)
        elif type_identifier == 'sma':
            __fromSMARTS(mol, identifier, _backend)
        else:
            raise NotImplementedError("Unknown identifier type {0}".format(type_identifier))

        if isCorrectlyParsed(mol, identifier):
            mol.updateAtomTypes()
            return mol
        else:
            logging.debug('Backend %s is not able to parse identifier %s', _backend, identifier)

    logging.error("Unable to correctly parse %s with backend %s", identifier, backend)
    raise Exception("Couldn't parse {0}".format(identifier))


def parse_openbabel(mol, identifier, type_identifier):
    """Converts the identifier to a Molecule using Openbabel."""
    obConversion = openbabel.OBConversion()
    obConversion.SetInAndOutFormats(type_identifier, "smi")  # SetInFormat(identifier) does not exist.
    obmol = openbabel.OBMol()
    obConversion.ReadString(obmol, identifier)
    obmol.AddHydrogens()
    obmol.AssignSpinMultiplicity(True)
    fromOBMol(mol, obmol)
    # mol.updateAtomTypes()
    return mol


def isCorrectlyParsed(mol, identifier):
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


def __lookup(mol, identifier, type_identifier):
    """
    Looks up the identifier and parses it the way we think is best.

    For troublesome inchis, we look up the smiles, and parse smiles.
    For troublesome smiles, we look up the adj list, and parse the adj list.

    """
    if type_identifier.lower() == 'inchi':
        try:
            smi = INCHI_LOOKUPS[identifier.split('/', 1)[1]]
            return mol.fromSMILES(smi)
        except KeyError:
            return None
    elif type_identifier.lower() == 'smi':
        try:
            adjList = SMILES_LOOKUPS[identifier]
            return mol.fromAdjacencyList(adjList)
        except KeyError:
            return None


def fromInChI(mol, inchistr, backend='try-all'):
    """
    Convert an InChI string `inchistr` to a molecular structure. Uses
    a user-specified backend for conversion, currently supporting
    rdkit (default) and openbabel.
    """

    mol.InChI = inchistr

    if inchiutil.INCHI_PREFIX in inchistr:
        return __parse(mol, inchistr, 'inchi', backend)
    else:
        return __parse(mol, inchiutil.INCHI_PREFIX + '/' + inchistr, 'inchi', backend)


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


def fromSMILES(mol, smilesstr, backend='try-all'):
    """
    Convert a SMILES string `smilesstr` to a molecular structure. Uses
    a user-specified backend for conversion, currently supporting
    rdkit (default) and openbabel.
    """
    return __parse(mol, smilesstr, 'smi', backend)


def fromSMARTS(mol, smartsstr, backend='rdkit'):
    """
    Convert a SMARTS string `smartsstr` to a molecular structure. Uses
    `RDKit <http://rdkit.org/>`_ to perform the conversion.
    This Kekulizes everything, removing all aromatic atom types.
    """

    return __parse(mol, smartsstr, 'sma', backend)


