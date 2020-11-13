from src.bph_co2.zone import ThermalZone
from src.bph_co2.wall import Wall
from src.bph_co2.ambient import Ambient
from src.bph_co2.ventilation import Ventilation
from src.bph_co2.timeseries import Timeseries
from src.bph_co2.solver import Solver

# create ambient

ambient = Ambient(name='outside',
                  theta=30)

ventilation = Ventilation(t_ex=ambient.theta)

# create walls:

zone = ThermalZone(volume=6 * 6 * 2.6,
                   ventilation=ventilation,
                   phi_int_c=4*200 + 4 * 100,
                   phi_hc_id=-1000)


window1 = Wall(theta_in=None,
               theta_out=ambient.theta,
               r_si=0.13,
               u=1,
               r_se=0.04,
               _orientation='vertical',
               name='windows',
               area=(1.6 * 1.3)*2,
               alpha_k=2.5,
               side1=zone)


outside_wall1 = Wall(theta_in=None,
                     theta_out=ambient.theta,
                     r_si=0.13,
                     u=0.35,
                     r_se=0.04,
                     _orientation='vertical',
                     name='outside walls',
                     area=6 * 2.6 * 2 - window1.area,
                     alpha_k=2.5,
                     side1=zone)

inside_wall1 = Wall(theta_in=None,
                    theta_out=None,
                    theta_s=24,
                    r_si=0.13,
                    u=0.2,
                    r_se=0.04,
                    _orientation='vertical',
                    name='inside walls',
                    area=6*2.6*2,
                    alpha_k=2.5,
                    side1=zone)

floor = Wall(theta_in=25,
             theta_out=15,
             u=0.35,
             r_se=0.04,
             orientation='floor',
             name='floor',
             area=5*5,
             side1=zone)

ceiling = Wall(theta_in=25,
               theta_out=ambient.theta,
               u=0.35,
               r_se=0.04,
               orientation='ceiling',
               name='ceiling',
               area=5*5,
               side1=zone)


res = zone.calc_steady_state_result()
print(res)

zone.theta_0 = 20

solver = Solver(zone=zone,
                timestep=1,
                t_end=26640
                )

t_transient = solver.calc_transient_room_temperature()


pass




