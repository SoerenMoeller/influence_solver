import math

from solver.constants import QUALITY_MONO, QUALITY_ANTI, QUALITY_CONS

# AC current as an influence model with time influencing voltage
# and voltage causing current via some resistance
# modelled at arbitrary degrees of granularity

resistance = 300
phase_granularity = 0.01
top_ac_voltage = 230
voltage_granularity = 30

peak_voltage = top_ac_voltage * math.sqrt(2)
peak_current = peak_voltage / resistance
pi = 3.1415
twopi = pi * 2
points = range(int(twopi / phase_granularity))
l = len(points)
tpoints = [t / l * twopi - pi for t in points]
current_model = set()
for t in tpoints:
    t1 = t - phase_granularity
    t2 = t + phase_granularity
    v1 = math.sin(t1) * peak_voltage
    v2 = math.sin(t2) * peak_voltage

    if v1 < v2:
        current_model.add(('time', (t1, t2), QUALITY_MONO, (v1, v2), 'voltage'))
    elif v2 < v1:
        current_model.add(('time', (t1, t2), QUALITY_ANTI, (v2, v1), 'voltage'))
    else:
        current_model.add(('time', (t1, t2), QUALITY_CONS, (v1, v1), 'voltage'))
points = range(int(2 * peak_voltage / voltage_granularity))
l = len(points)
vpoints = [v / l * 2 * peak_voltage - peak_voltage for v in points]
for v in vpoints:
    v1 = v - voltage_granularity
    v2 = v + voltage_granularity
    c1 = v1 / resistance
    c2 = v2 / resistance
    if c1 < c2:
        current_model.add(('voltage', (v1, v2), QUALITY_MONO, (c1, c2), 'current'))
    elif c2 > c1:
        current_model.add(('voltage', (v1, v2), QUALITY_ANTI, (c2, c1), 'current'))
    else:
        current_model.add(('voltage', (v1, v2), QUALITY_CONS, (c1, c1), 'current'))

current_model_statements = \
    [('time', (-pi, -pi / 2), QUALITY_ANTI, (-peak_current, 0), 'current'),
     ('time', (-pi / 2, pi / 2), QUALITY_MONO, (-peak_current, peak_current), 'current'),
     ('time', (pi / 2, pi), QUALITY_ANTI, (0, peak_current), 'current'),
     ('time', (-pi, -pi / 2 - 0.1), QUALITY_ANTI, (-peak_current - 0.2, 0.2), 'current')]
