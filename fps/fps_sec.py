class Security:
   @staticmethod
   def check_credentials(user_or_drone, name, psswd):
       return user_or_drone.name == name and user_or_drone.psswd == psswd
