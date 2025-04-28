# Food trucks in Korea

This repository contains a Python script to run a SUMO (Simulation of Urban MObility) scenario in which trucks provide serviced to nearby customers.
The script collects real-time data and uses an optimization solver to direct trucks to the next best location.

---

## Setup
1. Clone this repository
```bash
git clone git@github.com:2jungeuni/foodtruck-korea.git
cd foodtruck-korea
```

2. Get the Gurobi license

It is recommended to follow the installation instructions provided in the [video](https://www.youtube.com/watch?v=OYuOKXPJ5PI).

3. Install SUMO

It is recommended to follow the installation instructions provided in the official [SUMO documentation](https://sumo.dlr.de/docs/Installing/index.html).

4. Install dependencies
```bash
pip install traci sumolib
```

5. Configure SUMO

Ensure ```SUMO_HOME``` is set:
```bash
export SUMO_HOME=/path/to/sumo
export PATH=$PATH:$SUMO_HOME/bin:$SUMO_HOME/tools
```

6. Edit ```config.py```

Update the paths or parameters (e.g., ```sumo_config```, ```end```, ```interval```, etc.) to match your scenario.

---

## Usage
1. Run the simulation

Execute the main script:
```bash
python3 main.py
```

2. Simulation output

During execution, the script will print intermediate logs to the console and create a ```log.csv``` file in the current directory.

3. Customization

- Change the ***service distance*** from ```1000``` meters to a different radius by editing the conditional in the script.
- Modify the ***stop duration*** or insert additional stops based on your requirements.

---

## Results
1. Cumulative CO2 emissions of all food trucks during an hour.
<div align="center">
    <img src=figures/carbon_emission.png width="75%">
</div>

2. Change of service rate during an hour.
<div align="center">
    <img src=figures/service_rate.png width="75%">
</div>