# -*- coding: utf-8 -*-
"""
Created on Sat May 23 23:51:08 2026

@author: pantk
"""

# ============================================================
# REAL RC FRAME + INFILLS + SEMI-RIGID DIAPHRAGMS
# FINAL CORRECTED GEOMETRY
#
# Π1 : #2 → #3 → #5 → #4 → #6
# Π2 : #5 → #9 → #8 → #4
#
# OpenSeesPy / Spyder
# ============================================================

import openseespy.opensees as ops
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# RESET
# ============================================================

ops.wipe()

ops.model('basic', '-ndm', 2, '-ndf', 3)

# ============================================================
# ANALYSIS CASE
# ============================================================

CASE = 'HEALTHY'

# CASE = 'CRACKED'

# ============================================================
# MATERIALS
# ============================================================

Ec = 30e9
Em = 3e9

# diaphragm stiffness

Kd1 = 2e8
Kd2 = 2e8

if CASE == 'CRACKED':

    Kd1 *= 0.3
    Kd2 *= 0.3

# ============================================================
# STOREY HEIGHT
# ============================================================

H = 3.0

# ============================================================
# CORRECTED GEOMETRY
# ============================================================

# Π1:
#
# #6 ---- #4 ---- #5
# |                 |
# |                 |
# #2 ---- #3 -------#
#
# Π2:
#
# #5 ---- #9
# |        |
# #4 ---- #8

coords = {

    # Π1

    2:(0.00,0.00),

    3:(5.55,0.00),

    5:(5.55,4.45),

    4:(1.30,4.45),

    # CORRECTED #6 POSITION
    # κάτω από το #4

    6:(1.30,0.00),

    # Π2

    9:(9.60,4.45),

    8:(9.60,0.40)

}

# ============================================================
# CREATE NODES
# ============================================================

for n,(x,y) in coords.items():

    ops.node(n,x,y)

    ops.node(n+100,x,y+H)

# diaphragm control nodes

ops.node(1000,3.0,2.2+H)
ops.node(2000,7.5,2.4+H)

# ============================================================
# FIXITIES
# ============================================================

for n in coords.keys():

    ops.fix(n,1,1,1)

ops.fix(1000,0,1,1)
ops.fix(2000,0,1,1)

# ============================================================
# MASSES
# ============================================================

for n in coords.keys():

    ops.mass(n+100,1000,1000,1e-6)

# ============================================================
# TRANSFORMATION
# ============================================================

ops.geomTransf('Linear',1)

# ============================================================
# RC SECTIONS
# ============================================================

# columns 25x25

Acol = 0.25*0.25
Izcol = (0.25*0.25**3)/12

# beams 25x40

A2540 = 0.25*0.40
Iz2540 = (0.25*0.40**3)/12

# beams 15x40

A1540 = 0.15*0.40
Iz1540 = (0.15*0.40**3)/12

# beams 15x45

A1545 = 0.15*0.45
Iz1545 = (0.15*0.45**3)/12

# ============================================================
# COLUMNS
# ============================================================

etag = 1

for n in coords.keys():

    ops.element(
        'elasticBeamColumn',
        etag,
        n,
        n+100,
        Acol,
        Ec,
        Izcol,
        1
    )

    etag += 1

# ============================================================
# BEAMS
# ============================================================

beam_data = [

    # ========================================================
    # Π1
    # ========================================================

    (102,103,'D1.1 25/40',A2540,Iz2540),

    (103,105,'D1.2 25/40',A2540,Iz2540),

    (105,104,'D1.3 15/40',A1540,Iz1540),

    (104,106,'D1.4 15/40',A1540,Iz1540),

    (106,102,'D1.5 15/40',A1540,Iz1540),

    # ========================================================
    # Π2
    # ========================================================

    (105,109,'D2.1 25/40',A2540,Iz2540),

    (109,108,'D2.2 15/45',A1545,Iz1545),

    # CORRECTED:
    # horizontal #8-#4

    (108,104,'D2.3 15/45-15/60',A1545,Iz1545)

]

beam_labels = []

for ni,nj,label,A,Iz in beam_data:

    ops.element(
        'elasticBeamColumn',
        etag,
        ni,
        nj,
        A,
        Ec,
        Iz,
        1
    )

    beam_labels.append((ni,nj,label))

    etag += 1

# ============================================================
# MASONRY INFILLS
# ============================================================

ops.uniaxialMaterial(
    'Elastic',
    100,
    Em
)

Astrut = 0.15

struts = [

    # Π1 masonry

    (102,103,'INFILL P1'),
    (103,105,'INFILL P1'),

    # Π2 masonry

    (105,109,'INFILL P2'),
    (109,108,'INFILL P2')

]

for ni,nj,label in struts:

    ops.element(
        'truss',
        etag,
        ni,
        nj,
        Astrut,
        100
    )

    etag += 1

# ============================================================
# SEMI-RIGID DIAPHRAGMS
# ============================================================

ops.uniaxialMaterial('Elastic',200,Kd1)
ops.uniaxialMaterial('Elastic',201,Kd2)

# ------------------------------------------------------------
# Π1 diaphragm
# ------------------------------------------------------------

for n in [102,103,105,104,106]:

    ops.element(
        'twoNodeLink',
        etag,
        n,
        1000,
        '-mat',
        200,
        '-dir',
        1
    )

    etag += 1

# ------------------------------------------------------------
# Π2 diaphragm
# ------------------------------------------------------------

for n in [105,109,108,104]:

    ops.element(
        'twoNodeLink',
        etag,
        n,
        2000,
        '-mat',
        201,
        '-dir',
        1
    )

    etag += 1

# ============================================================
# LOADS
# ============================================================

ops.timeSeries('Linear',1)

ops.pattern('Plain',1,1)

Fx = 100e3

loaded_nodes = [102,103,105,104,106,109,108]

for n in loaded_nodes:

    ops.load(
        n,
        Fx/len(loaded_nodes),
        0,
        0
    )

# ============================================================
# ANALYSIS
# ============================================================

ops.system('BandGeneral')

ops.numberer('RCM')

ops.constraints('Plain')

ops.test(
    'NormDispIncr',
    1e-8,
    100
)

ops.algorithm('Linear')

ops.integrator(
    'LoadControl',
    1.0
)

ops.analysis('Static')

ok = ops.analyze(1)

print('\nANALYSIS STATUS =',ok)

# ============================================================
# RESULTS
# ============================================================

print('\nNODE DISPLACEMENTS\n')

for n in loaded_nodes:

    ux = ops.nodeDisp(n,1)

    print(
        'Node',
        n,
        'UX =',
        ux
    )

# ============================================================
# DIAPHRAGM DISTORTION
# ============================================================

distP1 = ops.nodeDisp(105,1) - ops.nodeDisp(102,1)

distP2 = ops.nodeDisp(108,1) - ops.nodeDisp(105,1)

print('\nP1 DIAPHRAGM DISTORTION =',distP1)

print('P2 DIAPHRAGM DISTORTION =',distP2)

# ============================================================
# MODAL ANALYSIS
# ============================================================

eig = ops.eigen(1)

w = np.sqrt(eig[0])

T = 2*np.pi/w

print('\nFUNDAMENTAL PERIOD T =',T)

# ============================================================
# PLOT
# ============================================================

plt.figure(figsize=(15,10))

scale = 100

# ============================================================
# ORIGINAL GEOMETRY
# ============================================================

for ni,nj,label in beam_labels:

    x1,y1 = ops.nodeCoord(ni)
    x2,y2 = ops.nodeCoord(nj)

    plt.plot(
        [x1,x2],
        [y1,y2],
        'b-',
        lw=3
    )

# ============================================================
# DEFORMED GEOMETRY
# ============================================================

for ni,nj,label in beam_labels:

    x1,y1 = ops.nodeCoord(ni)
    x2,y2 = ops.nodeCoord(nj)

    d1 = ops.nodeDisp(ni)
    d2 = ops.nodeDisp(nj)

    plt.plot(
        [x1+scale*d1[0],x2+scale*d2[0]],
        [y1+scale*d1[1],y2+scale*d2[1]],
        'r--',
        lw=2
    )

# ============================================================
# COLUMN LABELS
# ============================================================

for n,(x,y) in coords.items():

    plt.plot(
        x,
        y+H,
        'ko',
        ms=10
    )

    plt.text(
        x,
        y+H+0.15,
        f'#{n}\n25x25',
        fontsize=10,
        ha='center',
        bbox=dict(facecolor='white')
    )

# ============================================================
# BEAM LABELS
# ============================================================

for ni,nj,label in beam_labels:

    x1,y1 = ops.nodeCoord(ni)
    x2,y2 = ops.nodeCoord(nj)

    xm = (x1+x2)/2
    ym = (y1+y2)/2

    plt.text(
        xm,
        ym,
        label,
        fontsize=9,
        color='blue',
        bbox=dict(facecolor='white')
    )

# ============================================================
# MASONRY VISUALIZATION
# ============================================================

for ni,nj,label in struts:

    x1,y1 = ops.nodeCoord(ni)
    x2,y2 = ops.nodeCoord(nj)

    plt.plot(
        [x1,x2],
        [y1,y2],
        color='orange',
        ls=':',
        lw=5
    )

    xm = (x1+x2)/2
    ym = (y1+y2)/2

    plt.text(
        xm,
        ym+0.25,
        label,
        fontsize=10,
        color='darkorange',
        ha='center',
        bbox=dict(facecolor='white')
    )

# ============================================================
# SLAB LABELS
# ============================================================

plt.text(
    2.8,
    5.6,
    'SLAB P1\nh=18cm',
    fontsize=16,
    color='darkgreen',
    bbox=dict(facecolor='white')
)

plt.text(
    7.5,
    5.6,
    'SLAB P2\nh=18cm',
    fontsize=16,
    color='darkgreen',
    bbox=dict(facecolor='white')
)

# ============================================================
# STYLE
# ============================================================

plt.grid(True)

plt.axis('equal')

plt.xlabel('X (m)',fontsize=14)

plt.ylabel('Y (m)',fontsize=14)

plt.title(
    f'RC FRAME + MASONRY INFILLS + SEMI-RIGID DIAPHRAGMS ({CASE})',
    fontsize=18
)

plt.show()