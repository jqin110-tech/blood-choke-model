# The physiology in plain English

*Educational modelling notes, not medical advice. Source tags (S1, S5, ...)
refer to [SOURCES.md](SOURCES.md).*

The brain runs almost entirely on oxygen delivered by blood, and it keeps
very little in reserve. In healthy adults, blood flows through brain tissue at
roughly 44–50 ml per 100 g (or 100 ml) of tissue per minute (S4, S5), and the
tissue burns about 3.3 ml of oxygen per 100 ml per minute (S5). Only about 44%
of the oxygen arriving in arterial blood is pulled out on each pass (S5), so
the blood leaving the brain still carries most of its oxygen. That spare
oxygen, sitting in the roughly 3.8 ml of blood held inside each 100 ml of
brain tissue (S5), is the brain's main short-term buffer. A back-of-envelope
check from those same numbers suggests the buffer lasts on the order of ten
seconds, which is why timing matters so much here; stage 2 will turn that into
a proper calculation.

Blood reaches the brain through four arteries. About three quarters of the
flow comes up the two internal carotid arteries in the front of the neck, and
about a quarter comes up the two vertebral arteries, which run through the
bones of the spine (S9: 72% vs 28% in 94 people; S6 and S7 give similar
splits). A blood
choke compresses the carotids. In the one modern human study we could open,
neck restraint cut the velocity of blood in the middle cerebral arteries to
about a fifth of normal while arterial blood pressure and heart rate did not
change significantly (S3). The authors conclude that the main cause of
unconsciousness was reduced brain blood flow, not a reflex slowing of the
heart (S3).

The observed timings are short and consistent. In the 1940s Red Wing
experiments, a cuff inflated around the neck stopped blood flow almost
completely, and consciousness was lost after 4 to 10 seconds; it returned 3 to
11.5 seconds after release (S1, S2). In the 2012 study, the eyes became fixed
after 9.5 ± 0.4 (SE) seconds according to its abstract (S3), although a later
paper cites the same study as 7.9 seconds (S10), and we could not open the
full text to settle which is right. In the earlier work, fixation came half a
second to a second before loss of consciousness (S1). A 2021 review gives the
same picture: function fails once flow drops below about 22 ml/100 g/min, and
consciousness is often lost within 10 seconds (S4).

So the story the model will test is simple: cutting carotid flow lowers oxygen
delivery below consumption, the small store of oxygen in the brain's blood
runs down, and once it drops far enough, the brain stops supporting
consciousness. What the sources do **not** give us directly is how low "far
enough" is, expressed as an oxygen level. That is the biggest open gap (see
SOURCES.md, Gaps).
