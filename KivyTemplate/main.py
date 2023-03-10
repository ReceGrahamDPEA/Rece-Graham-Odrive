import os
import sys

# os.environ['DISPLAY'] = ":0.0"
# os.environ['KIVY_WINDOW'] = 'egl_rpi'

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.properties import ObjectProperty

from pidev.MixPanel import MixPanel
from pidev.kivy.PassCodeScreen import PassCodeScreen
from pidev.kivy.PauseScreen import PauseScreen
from pidev.kivy import DPEAButton
from pidev.kivy import ImageButton
from pidev.Joystick import Joystick

from examples.joystick import *

sys.path.append("/home/soft-dev/Documents/dpea-odrive/")
from odrive_helpers import *

MIXPANEL_TOKEN = "x"
MIXPANEL = MixPanel("Project Name", MIXPANEL_TOKEN)

SCREEN_MANAGER = ScreenManager()
MAIN_SCREEN_NAME = 'main'
TRAJ_SCREEN_NAME = 'traj'
GPIO_SCREEN_NAME = 'gpio'
ADMIN_SCREEN_NAME = 'admin'

od = find_odrive()
ax = ODriveAxis(od.axis0)

joy = Joystick(number=0, ssh_deploy=True)


class ProjectNameGUI(App):
    """
    Class to handle running the GUI Application
    """

    def __init__(self, **kw):
        super().__init__(**kw)
        assert od.config.enable_brake_resistor is True, "Check for faulty brake resistor."

        ax.set_gains()
        if not ax.is_calibrated():
            print("calibrating...")
            ax.calibrate()

    def build(self):
        """
        Build the application
        :return: Kivy Screen Manager instance
        """
        return SCREEN_MANAGER


Window.clearcolor = (1, 1, 1, 1)  # White


class MainScreen(Screen):
    """
    Class to handle the main screen and its associated touch events
    """

    def __init__(self, **kw):
        super().__init__(**kw)
        print("Starting up!")

    def switch_to_traj(self):
        SCREEN_MANAGER.transition.direction = "left"
        SCREEN_MANAGER.current = TRAJ_SCREEN_NAME

    def switch_to_gpio(self):
        SCREEN_MANAGER.transition.direction = "right"
        SCREEN_MANAGER.current = GPIO_SCREEN_NAME

    def admin_action(self):
        """
        Hidden admin button touch event. Transitions to passCodeScreen.
        This method is called from pidev/kivy/PassCodeScreen.kv
        :return: None
        """
        SCREEN_MANAGER.current = 'passCode'

    def quit(self):
        quit()

class TrajectoryScreen(Screen):
    """
    Class to handle the trajectory control screen and its associated touch events
    """

    def __init__(self, **kw):
        super().__init__(**kw)

        start_joy_thread(0)

    def switch_screen(self):
        SCREEN_MANAGER.transition.direction = "right"
        SCREEN_MANAGER.current = MAIN_SCREEN_NAME

    def simple_velocity(self):
        # SETTING VELOCITY
        print("Current Position in Turns = ", round(ax.get_pos(), 2))
        ax.set_vel_limit(5)  # Sets the velocity limit to be X turns/s
        ax.set_vel(3)  # Starts turning the motor X turns/s
        sleep(5)
        print("Encoder Measured Velocity = ", round(ax.get_vel(), 2))
        ax.set_vel(0)  # Stops motor
        sleep(1)
        print("Current Position in Turns = ", round(ax.get_pos(), 2))
        ax.set_pos(0)
        ax.wait_for_motor_to_stop()
        print("Current Position in Turns = ", round(ax.get_pos(), 2))
        sleep(3)

    def joy_update(self):

        joy_action(0)

class GPIOScreen(Screen):
    """
    Class to handle the GPIO screen and its associated touch/listening events
    """

    def switch_screen(self):
        SCREEN_MANAGER.transition.direction = "left"
        SCREEN_MANAGER.current = MAIN_SCREEN_NAME


class AdminScreen(Screen):
    """
    Class to handle the AdminScreen and its functionality
    """

    def __init__(self, **kwargs):
        """
        Load the AdminScreen.kv file. Set the necessary names of the screens for the PassCodeScreen to transition to.
        Lastly super Screen's __init__
        :param kwargs: Normal kivy.uix.screenmanager.Screen attributes
        """
        Builder.load_file('AdminScreen.kv')

        PassCodeScreen.set_admin_events_screen(
            ADMIN_SCREEN_NAME)  # Specify screen name to transition to after correct password
        PassCodeScreen.set_transition_back_screen(
            MAIN_SCREEN_NAME)  # set screen name to transition to if "Back to Game is pressed"

        super(AdminScreen, self).__init__(**kwargs)

    @staticmethod
    def transition_back():
        """
        Transition back to the main screen
        :return:
        """
        SCREEN_MANAGER.current = MAIN_SCREEN_NAME

    @staticmethod
    def shutdown():
        """
        Shutdown the system. This should free all steppers and do any cleanup necessary
        :return: None
        """
        os.system("sudo shutdown now")

    @staticmethod
    def exit_program():
        """
        Quit the program. This should free all steppers and do any cleanup necessary
        :return: None
        """
        quit()


"""
Widget additions
"""

Builder.load_file('main.kv')
SCREEN_MANAGER.add_widget(MainScreen(name=MAIN_SCREEN_NAME))
SCREEN_MANAGER.add_widget(TrajectoryScreen(name=TRAJ_SCREEN_NAME))
SCREEN_MANAGER.add_widget(GPIOScreen(name=GPIO_SCREEN_NAME))
SCREEN_MANAGER.add_widget(PassCodeScreen(name='passCode'))
SCREEN_MANAGER.add_widget(PauseScreen(name='pauseScene'))
SCREEN_MANAGER.add_widget(AdminScreen(name=ADMIN_SCREEN_NAME))

"""
MixPanel
"""


def send_event(event_name):
    """
    Send an event to MixPanel without properties
    :param event_name: Name of the event
    :return: None
    """
    global MIXPANEL

    MIXPANEL.set_event_name(event_name)
    MIXPANEL.send_event()


if __name__ == "__main__":
    # send_event("Project Initialized")
    # Window.fullscreen = 'auto'
    ProjectNameGUI().run()
