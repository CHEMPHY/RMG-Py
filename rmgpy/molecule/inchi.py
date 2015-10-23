import re

INCHI_PREFIX = 'InChI=1'

"""

The prefix with the multiplicity information.

For example, a triplet biradical will bear the 
following multiplicity layer in the augmented InChI:

InChI=1/.../mult3

The singlet equivalent of aforementioned biradical has the following
augmented InChI:

InChI=1/.../mult1

"""
MULT_PREFIX = '/mult'



"""
The prefix with the information on the distribution of unpaired electrons across the atoms.

For example, a triplet biradical with unpaired electrons on atom 1 and atom 3 
will have the following unpaired electron layer in the augmented InChI:

InChI=1/.../mult3/u1,3

The indices refer to the 1-based indices in the InChI string (NOT the 0-based
    indices of the Molecule container!)

"""
U_LAYER_PREFIX = '/u'

"""The separator that separates the indices of the atoms that bear unpaired electrons."""
U_LAYER_SEPARATOR = ','

def decompose(string):
    """
    Converts an augmented inchi into an inchi, multiplicity and indices array for the atoms
    bearing unpaired electrons.

    returns: 
    - multiplicity (int)
    - indices array for the atoms bearing unpaired electrons.

    """

    if not MULT_PREFIX in string:
        return string, None, []

    inchi, mult_ulayer = string.split(MULT_PREFIX)
    
    if not U_LAYER_PREFIX in mult_ulayer:
        mult = int(mult_ulayer)
        u_indices = []    
        return inchi, mult, u_indices

    mult, ulayer = mult_ulayer.split(U_LAYER_PREFIX)
    mult = int(mult)
    u_indices = [int(i) for i in ulayer.split(U_LAYER_SEPARATOR)]
    return inchi, mult, u_indices

def ignore_prefix(string):
    """
    Splits off the 'InChI=1S' or 'InChI=1' layer of an InChI
    and returns the last part.
    """

    if not INCHI_PREFIX in string:
        raise InchiException('Not a valid InChI: {}'.format(string))

    return re.split(r"(InChI=1+)(S*)/", string)[-1]

def compose_aug_inchi(inchi, mult_layer, ulayer=None):
    prefix = INCHI_PREFIX + '/' if not INCHI_PREFIX in inchi else ''
    if ulayer is not None:
        return prefix + inchi + mult_layer + ulayer
    else:
        return prefix + inchi + mult_layer 


def compose_aug_inchi_key(inchi_key, mult_layer, ulayer=None):
    if ulayer is not None:
        return inchi_key + mult_layer + ulayer
    else:
        return inchi_key + mult_layer 

def parse_H_layer(inchi):
    """
    Converts the Mobile H layer of an inchi string into a 
    list of atom indices couples that carry a mobile hydrogen.

    Example:
    The hydrogen of the hydroxyl group can migrate to the carbonyl 
    oxygen.

    O=C-O
    InChI=1S/CH2O2/c2-1-3/h1H,(H,2,3)

    The atoms bearing a mobile hydrogen will be found in
    the hydrogen layer, within the parentheses.

    An empty list will be returned when there are no mobile hydrogens.

    """
    pieces = inchi.split('/')
    h_layer = None
    for piece in pieces:
        if piece.startswith('h'):
            h_layer = piece
            break
    else: 
        raise Exception('Could not find the hydrogen layer in the inchi: {}'.format(inchi))

    # search for (*) pattern
    pattern = re.compile( r'\((.[^\(\)]*)\)')

    couples = []
    for match in re.findall(pattern, h_layer):
        mobile_h_atoms = map(int, match[2:].split(','))
        couples.append(mobile_h_atoms)

    return couples

def parse_E_layer(auxinfo):
    """
    Converts the layer with equivalence information (E-layer) 
    on atoms into a list of lists of equivalent atom indices.

    Example:
    Auxiliary info of InChI=1S/C8H14/c1-5-7(3)8(4)6-2/h5-8H,1-2H2,3-4H3:
    AuxInfo=1/0/N:1,8,4,6,2,7,3,5/E:(1,2)(3,4)(5,6)(7,8)/rA:8C.2C.2CCCCCC/rB:s1;s2;s3;s3;s5;s5;d7;/rC:;;;;;;;;
    E-layer: 

    /E:(1,2)(3,4)(5,6)(7,8)/

    denotes that atoms (1,2), (3,4), (5,6), (7,8) are equivalent and cannot be distinguished based on the 
    implemented canonicalization algorithm.

    Returned object:

    [[1,2],[3,4],[5,6],[7,8]]

    Returns an empty list of the E-layer could not be found.

    """

    pieces = auxinfo.split('/')
    e_layer = None
    for piece in pieces:
        if piece.startswith('E'):
            e_layer = piece[2:]#cut off /E:
            break
    else:
        return []

    # search for (*) pattern
    pattern = re.compile( r'\((.[^\(\)]*)\)')

    equivalent_atoms = []
    for atomtuple in re.findall(pattern, e_layer):
        indices = list(map(int, atomtuple.split(',')))
        equivalent_atoms.append(indices)

    return equivalent_atoms
    
class InchiException(Exception):
    pass

class InChI(str):
    """InChI is a type of string in which the InChI=1 prefix is ignored."""
    def __new__(self, inchi):

      if not INCHI_PREFIX in inchi:
        raise InchiException('Not a valid InChI: {}'.format(inchi))

      return str.__new__(self, ignore_prefix(inchi))

class AugmentedInChI(InChI):
    """AugmentedInChI is an InChI with inchi, multiplicity and unpaired electron attributes."""
    def __init__(self, aug_inchi):
        super(AugmentedInChI, self).__init__()
        inchi, mult, u_indices = decompose(self)

        self.inchi = str(inchi)

        # default to multiplicity -1
        self.mult = mult or -1

        # default to None
        self.u_indices = u_indices or None
        
