# The project in plain English

*Educational modelling project, not medical advice. It describes physiology
and a model, and gives no guidance on applying chokes or strikes. Every
number below is printed by a script into `results/`; a test fails if this
file states one that is not.*

## What it is

A blood choke squeezes the two carotid arteries in the neck, which carry
most of the brain's blood. Within seconds the person loses consciousness.
This project asks whether that timing is what you get from the simplest
possible bookkeeping of oxygen.

The model is one box. The box holds the oxygen in the blood that is inside
the brain at this moment. Oxygen comes in with arterial blood, goes out with
venous blood, and is used up by the tissue. When a choke cuts the flow in,
the tissue keeps using oxygen, so the box drains. The model calls the person
unconscious when the box falls below a set level.

Five inputs are measured values from published studies of healthy brains:
blood flow, blood volume, oxygen use, the share of oxygen extracted, and how
flow is split between the carotid and vertebral arteries. One input, the
level at which consciousness is lost, could not be found in any source, so
it is fitted to one experiment from 1943. Everything after that is a test on
data the fit never saw.

It passes some tests and fails one. For 81 chokes timed from video in UFC
fights, the measured mean is 9.0 s with a 95% interval of 8.3 to 9.9 s, and
the model says 8.6 s. For a 2012 laboratory study it is within about one and
a half seconds. But for waking up after release, the model says 0.2 to 1.0 s
and the people measured took 3 to 11.5 s. The model is wrong there, and the
repo says so in the same place and at the same size as the passes.

It is not a simulation of neurons, and it does not explain consciousness. It
shows that oxygen running out is fast enough to account for the time to go
out, and that oxygen coming back is too fast to account for the time to wake
up.

## Things that went wrong along the way

All four are in the repo's history.

- **A conclusion written before the numbers.** The first draft of the
  recovery report said the model fails "whatever the inputs". The Monte
  Carlo then showed the slowest possible recovery reaches the fastest
  measured time in 17.2% of draws. The sentence was wrong and was rewritten
  to say what the numbers say.
- **A solver stepping across a jump.** Flow changes abruptly when a choke
  starts and stops. Integrating straight across that gives small timing
  errors, so the solver is restarted at each switch time.
- **A rounding bug.** A shortest-path search stored distances as 32-bit
  numbers and compared them with 64-bit ones, so almost every point was
  skipped as "already better". Storing both at the same precision fixed it.
- **A legend covering data.** One figure's legend hid three of the points it
  described. It was caught by looking at the figure, not by a test.
