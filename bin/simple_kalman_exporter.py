# Copyright (c) 2019 Daniel Hammer. All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
from matplotlib import pyplot as plt
import numpy as np

from simple_kalman_sim import SimpleKalmanSim
from simple_kalman_bag import SimpleKalmanBag

class SimpleKalmanExporter:
    def __init__(self, bag_path="", window="", ratio=1/3., plot=False):
        self.bag_path = bag_path
        self.window = window
        self.ratio = ratio
        self.plot = plot

        self.N = 200
        self.sim_time = 5.0
        self.peak_vel = 0.14
        self.window_size = 5
        self.window_list = ["sig", "exp"]
        self.adapt = False

        self.simple_kalman = None

    def run(self):

        # check window function
        if self.window == "":
            self.adapt = False
        elif self.window in self.window_list:
            self.adapt = True

        # check if sim or rosbag
        if self.bag_path == "":
            self.set_sim_params()
        else:
            self.set_bag_params()

        # plot or export
        if self.plot is True:
            self.plot_all()
        else:
            self.export_plots()

    def set_sim_params(self):
        self.simple_kalman = SimpleKalmanSim(
            N=self.N,
            sim_time=self.sim_time,
            peak_vel=self.peak_vel,
            ratio=self.ratio,
            window=self.window,
            window_size=self.window_size,
            adapt=self.adapt
        )
        self.simple_kalman.run_filter()

    def set_bag_params(self):
        self.simple_kalman = SimpleKalmanBag(
            bag_path=self.bag_path,
            ratio=self.ratio,
            window=self.window,
            window_size=self.window_size,
            adapt=self.adapt
        )
        self.simple_kalman.read_imu("/imu")
        self.simple_kalman.read_twist("/fake_wheel/twist")
        self.simple_kalman.upscale_twist()
        self.simple_kalman.run_filter()

    def type_check(self):
        type = "none"
        if isinstance(self.simple_kalman, SimpleKalmanSim):
            type = "sim"
        elif isinstance(self.simple_kalman, SimpleKalmanBag):
            type = "real"
        return type

    def plot_all(self):

        plt.figure(1)

        plt.subplot(511)
        plt.xlabel("Time in s")
        plt.ylabel("Velocity in m/s")
        plt.plot(self.simple_kalman.kalman.plot_t,self.simple_kalman.kalman.plot_u0)

        plt.subplot(512)
        plt.xlabel("Time in s")
        plt.ylabel("Acceleration in m/s^2")
        plt.plot(self.simple_kalman.kalman.plot_t,self.simple_kalman.kalman.plot_a)

        plt.subplot(513)
        plt.xlabel("Time in s")
        plt.ylabel("Distance in m")
        plt.plot(self.simple_kalman.kalman.plot_t,self.simple_kalman.kalman.plot_y)

        plt.subplot(514)
        plt.xlabel("Time in s")
        plt.ylabel("Velocity in m/s")
        plt.plot(self.simple_kalman.kalman.plot_t,self.simple_kalman.kalman.plot_v)
        plt.ticklabel_format(axis='both', style='plain')

        plt.subplot(515)
        plt.xlabel("Time in s")
        plt.ylabel("Ratio")
        fill = len(self.simple_kalman.kalman.plot_t) - len(self.simple_kalman.kalman.ratio_a)
        full_ratio_array = np.insert(self.simple_kalman.kalman.ratio_a, 0, np.full((fill),self.ratio))
        plt.plot(self.simple_kalman.kalman.plot_t,full_ratio_array)

        plt.show()

    def export_plots(self):

        type = self.type_check()
        b = 100
        e = 50

        new_t_array = []
        for elem in self.simple_kalman.kalman.plot_t:
            new_t_array.append(elem - self.simple_kalman.kalman.plot_t[b])

        self.simple_kalman.kalman.plot_t = new_t_array

        np.savetxt("plots/{}_input_vel.csv".format(type), np.transpose([self.simple_kalman.kalman.plot_t[b:-e], self.simple_kalman.kalman.plot_u0[b:-e]]) ,header='t u0', comments='# ',delimiter=' ', newline='\n')

        np.savetxt("plots/{}_input_accel.csv".format(type), np.transpose([self.simple_kalman.kalman.plot_t[b:-e], self.simple_kalman.kalman.plot_a[b:-e]]) ,header='t a', comments='# ',delimiter=' ', newline='\n')

        np.savetxt("plots/{}_robot_dist_{}.csv".format(type,self.window), np.transpose([self.simple_kalman.kalman.plot_t[b:-e],self.simple_kalman.kalman.plot_y[b:-e]]) ,header='t y', comments='# ',delimiter=' ', newline='\n')

        np.savetxt("plots/{}_robot_vel_{}.csv".format(type,self.window), np.transpose([self.simple_kalman.kalman.plot_t[b:-e],self.simple_kalman.kalman.plot_v[b:-e]]) ,header='t v', comments='# ',delimiter=' ', newline='\n')

        fill = len(self.simple_kalman.kalman.plot_t) - len(self.simple_kalman.kalman.ratio_a)
        full_ratio_array = np.insert(self.simple_kalman.kalman.ratio_a, 0, np.full((fill),self.simple_kalman.kalman.ratio))

        np.savetxt("plots/{}_robot_ratio_{}.csv".format(type,self.window), np.transpose([self.simple_kalman.kalman.plot_t[b:-e],full_ratio_array[b:-e]]) ,header='t r', comments='# ',delimiter=' ', newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Export plots")
    parser.add_argument("-b", "--bag", type=str, default="",help="Rosbag file path")
    parser.add_argument("-r", "--ratio", type=float, default=1/3., help="Covariance ratio")
    parser.add_argument("-w", "--window", type=str, help="Window type: sig or exp")
    parser.add_argument("-p", "--plot", action="store_true", help="Plot instad of export")
    args = parser.parse_args()

    simple_kalman_exporter = SimpleKalmanExporter(
        bag_path = args.bag,
        ratio=args.ratio,
        window=args.window,
        plot=args.plot
    )
    simple_kalman_exporter.run()
