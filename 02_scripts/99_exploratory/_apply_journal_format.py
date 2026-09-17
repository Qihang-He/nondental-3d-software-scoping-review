# -*- coding: utf-8 -*-
"""Journal-standard formatting pass on the manuscript.

1. trim the main text
2. remove every bold marker (the journal text should not carry decorative bold)
3. renumber the references so that they follow the order of first citation, and
   reorder the reference list accordingly
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
D = os.path.join('01_投稿文件', 'R2_草稿')
MS_P = os.path.join(D, 'Revised_manuscript_R2.md')
REF_P = os.path.join(D, 'References_R2.md')

ms = open(MS_P, encoding='utf-8').read()
ref = open(REF_P, encoding='utf-8').read()

# ---------------------------------------------------------------- 1. trims
TRIMS = [
    ("The trend is based on the 810 studies whose records carry a month-level publication date; the remaining 43 records carry only a year and are not plotted (Figure 2a).",
     "The trend uses the 810 records with a month-level date; the remaining 43 carry only a year (Figure 2a)."),
    ("Among the studies that illustrate the last group, condylar morphometry, palatal-rugae superimposition and forensic identification were all performed with nondental tools [12,20,21,22].",
     ""),
    ("Clustering the charted metadata identified four workflow archetypes (Figure 4). The largest, *image segmentation and 3D reconstruction* (325 studies, 38.1%), combines image segmentation with morphometric and phenotypic analysis and relies mainly on medical image-processing and general-purpose modelling software; it is the archetype with the largest clinical component. *Quantitative measurement and accuracy assessment of 3D data* (243 studies, 28.5%) is dominated by a single scenario and by reverse-engineering and metrology software, and is predominantly a laboratory activity. The *computational biomechanical simulation* archetype (178 studies, 20.9%) is the most homogeneous, being built around engineering simulation packages and comprising almost exclusively computational work. *Digital design and manufacturing* (107 studies, 12.5%) links general-purpose modelling with reverse-engineering and additive manufacturing, and has a larger technical-note component than the other groups. The four groups differ in both their scenario composition and their software families, which supports the view that the task at hand governs the choice of nondental tool, while the clinical discipline does not. Educational and case-report work, though few in number, illustrates how the same tools are repurposed for teaching and for individualised prosthetic or surgical planning [19,48,49].",
     "Clustering the charted metadata identified four workflow archetypes (Figure 4). The largest, *image segmentation and 3D reconstruction* (325 studies, 38.1%), combines image segmentation with morphometric and phenotypic analysis, relies mainly on medical image-processing and general-purpose modelling software, and has the largest clinical component. *Quantitative measurement and accuracy assessment of 3D data* (243 studies, 28.5%) addresses a single scenario and relies on reverse-engineering and metrology software, and is predominantly a laboratory activity. The *computational biomechanical simulation* archetype (178 studies, 20.9%) is the most homogeneous, being built around engineering simulation packages. *Digital design and manufacturing* (107 studies, 12.5%) links general-purpose modelling with reverse engineering and additive manufacturing. The four groups differ in both scenario composition and software families, which supports the view that the task at hand governs the choice of nondental tool, while the clinical discipline does not. Educational and case-report work illustrates how the same tools are repurposed for teaching and for individualised planning [19,48,49]."),
    ("These tools are rarely used alone: more than a third of studies combined several packages, and the recurring combinations fall into a small number of functional patterns, a structure that idiosyncratic tool choice would not produce.",
     "These tools are rarely used alone: more than a third of studies combined several packages, and the recurring combinations fall into a small number of functional patterns."),
    ("If nondental tools are valued chiefly as complementary components that extend an existing digital ecosystem, then interoperability and standardised data exchange become the principal technical requirements, and the search for a single all-in-one solution is likely to be less productive than the deliberate design of well-documented, interoperable pipelines. The co-occurrence structure observed here points in that direction: segmentation packages are repeatedly paired with modelling environments, and design environments with simulation packages.",
     "If nondental tools are valued chiefly as complements that extend an existing digital ecosystem, interoperability and standardised data exchange become the principal technical requirements, and the search for a single all-in-one solution is likely to be less productive than designing well-documented, interoperable pipelines. The observed co-occurrence structure points that way: segmentation packages are repeatedly paired with modelling environments, and design environments with simulation packages."),
    ("The code list and the per-study coding output are provided in Supplementary File 2; because the scheme was applied to titles and abstracts, the frequencies describe the elements that authors considered salient enough to state at the outset, and qualifications given only in the body of the full text are not represented.",
     "The code list and the per-study coding output are provided in Supplementary File 2; because the scheme was applied to titles and abstracts, the frequencies describe what authors considered salient enough to state at the outset."),
    ("The reverse application of the same full-text standard to the previously included set also confirmed that four annotated packages could not be substantiated and that three software annotations required correction.",
     "The reverse application of the same standard also confirmed that four annotated packages could not be substantiated and that three software annotations required correction."),
    ("Because conference proceedings are counted separately from journals, the journal count is not used as a denominator for any proportion.",
     "Conference proceedings are counted separately from journals, so the journal count is not used as a denominator."),
    ("The archetypes are algorithmic groupings reproducible from the deposited dataset rather than manually coded categories, and software co-occurrence was quantified as supporting evidence.",
     "The archetypes are algorithmic groupings reproducible from the deposited dataset rather than manually coded categories."),
    ("Every package recorded in the review was verified against this definition, and a package was retained only if it was a named third-party product of nondental origin that is itself a 3D software package; general-purpose programming, numerical-computing and machine-learning platforms and programming libraries were therefore excluded, as were two packages developed specifically for dentistry.",
     "Every package recorded in the review was verified against this definition; a package was retained only if it was a named third-party product of nondental origin that is itself a 3D software package, so programming, numerical-computing and machine-learning platforms and libraries were excluded, as were two packages developed specifically for dentistry."),
    ("Reviews (narrative, systematic, scoping and meta-analyses), editorials, commentaries, conference abstracts, preprints and video articles were excluded, as were studies that used only dental-specific software and studies without 3D data processing.",
     "Reviews, editorials, commentaries, conference abstracts, preprints and video articles were excluded, as were studies that used only dental-specific software and studies without 3D data processing."),
    ("The definition therefore includes both commercial and open-source tools and is independent of cost or licensing model.",
     "The definition therefore includes commercial and open-source tools and is independent of cost or licensing model."),
]

missed = []
for old, new in TRIMS:
    pat = re.compile(r'\s+'.join(re.escape(w) for w in old.split()))
    if pat.search(ms):
        ms = pat.sub(lambda _m: new, ms, count=1)
    else:
        missed.append(old[:70])
print('trims applied: %d/%d' % (len(TRIMS) - len(missed), len(TRIMS)))
for m in missed:
    print('   NOT FOUND:', m)

# ---------------------------------------------------------------- 2. no bold
n_bold = len(re.findall(r'\*\*', ms))
ms = ms.replace('**', '')
print('bold markers removed from the manuscript:', n_bold)

# ---------------------------------------------------------------- 3. renumber
body = ms[:ms.index('## Figure legends')]
legends = ms[ms.index('## Figure legends'):]

cites = []


def expand(txt):
    out = []
    for part in re.split(r'\s*,\s*', txt):
        part = part.strip()
        if re.match(r'^\d+$', part):
            out.append(int(part))
        elif re.match(r'^\d+\s*[–-]\s*\d+$', part):
            a, b = re.split(r'\s*[–-]\s*', part)
            out.extend(range(int(a), int(b) + 1))
    return out


for m in re.finditer(r'\[(\d+(?:\s*[,–-]\s*\d+)*)\]', body):
    cites.extend(expand(m.group(1)))

order, seen = [], set()
for c in cites:
    if c not in seen:
        seen.add(c)
        order.append(c)

old2new = {o: i + 1 for i, o in enumerate(order)}
listed = [int(m.group(1)) for m in re.finditer(r'^\[(\d+)\]', ref, re.M)]
assert sorted(order) == sorted(listed), 'citation set and reference list differ'


def render(nums):
    nums = sorted(set(nums))
    parts, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        run = nums[j] - nums[i] + 1
        if run >= 4:
            parts.append('%d\u2013%d' % (nums[i], nums[j]))
            i = j + 1
        else:
            while i <= j:
                parts.append(str(nums[i]))
                i += 1
    return '[' + ','.join(parts) + ']'


new_body = re.sub(r'\[(\d+(?:\s*[,–-]\s*\d+)*)\]',
                  lambda m: render([old2new[x] for x in expand(m.group(1))]), body)
ms = new_body + legends

entries = {}
for line in ref.splitlines():
    m = re.match(r'^\[(\d+)\]\s*(.*)$', line)
    if m:
        entries[int(m.group(1))] = m.group(2).strip()
head = ref[:ref.index('[1]')].rstrip()
reordered = [head, '']
for new_no, old_no in enumerate(order, 1):
    reordered.append('[%d] %s' % (new_no, entries[old_no]))
open(REF_P, 'w', encoding='utf-8').write('\n'.join(reordered) + '\n')

open(MS_P, 'w', encoding='utf-8').write(ms)

print()
print('references renumbered: %d entries' % len(order))
print('first 15 in new order      :', order[:15])
print('sample: old [54] -> new [%d], old [45] -> new [%d], old [12] -> new [%d]'
      % (old2new[54], old2new[45], old2new[12]))
