# vRealize Operations Manager Self-monitoring Metric Collector


vRealize Operations Manager Self-monitoring Metric Collector(i.e vR Ops SMMC) is a 
custom metric collector of self-monitoring objects using vR Ops REST API.

## How it works

1. Loads credentials and object list `.json` data in commandline
2. Makes REST calls to GET information about vR Ops cluster status and bearer token
3. Makes REST calls to GET all self-monitoring object metrics including KPIs
4. Saves output data as `.csv` file with node name mentioned in filename



#### How to run
vR Ops SMMC is a command line tool.

It takes 3 command line arguments: 
1. `-CRED <request_cred_filepath>` vR Ops credentials file path
2. `-OBJ-LIST <object_list_filepath>` vR Ops self-monitoring object list file path
3. `-REP-DIR <report_directory_path>` Directory path in which reports would be saved

#### Running info

1. Clone/download the `code` of vR Ops Health Checker into the folder `<folder_name>`. 

2. Modify `inputs/request_cred.json` credentials file with your vR Ops credentials and report parameters 
(e.g. begin: start date of reporting period, end: end date of reporting period).

3. Install the dependent python libraries, by the following command:

```bash
cd <folder_name>
pip3 install -r requirements.txt
```

Run the script by the following command: 

```bash
cd <folder_name>
python3 run.py -CRED "<request_cred_filename>" -OBJ-LIST <object_list_filename> -REP-DIR <report_directory_path>
```

Example of run command: 

```bash
cd <folder_name>
python3 run.py -CRED "inputs/request_cred.json" -OBJ-LIST "inputs/object_list.json" -REP-DIR "reports"
```

NOTE: You will find the generated `.csv` metric data in `reports_<master_node_ip>` repository.

## About
vR Ops SMMC is written in python 3. [Version: `0.2`]
