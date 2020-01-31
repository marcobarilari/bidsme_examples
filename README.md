This folder contains toy datasets inspired from real ones but with removed 
data and keeping meta-information to minimum. The demographic informations
and subjects id are randomised.

Each example folder contains 3 subfolders:
 - source, containing the original toy dataset
 - renamed, containing sorted dataset
 - bids, containing bidsified dataset
 - resources, containing all nessesairy plugins and files to run the example

## Example 1
Example 1 is based on unpublished study on effet of fatigue on memory performance.

### How to run
First prepare data from `source` and place it to `renamed`
```
python3 $PATH/coinsort.py -r "nii" -t "MRI" example1/source/ example1/renamed/ -p example1/resources/plugins/rename_plugin.py
```

Next generate an `bidsmap.yaml` configuration file:
```
python $PATH/bidsmapper.py example1/renamed/ example1/bids -p example1/resources/plugins/bidsify_plugin.py
```

The generated file will be placed to `example1/bids/code/bidscoin/bidsmap.yaml`.
The initial run of `bidsmap` will produce a lot of warnings (> 500), listing
all nessesary modifications to apply to `bidsmap.yaml` configuration file.
For conviniance, the warnings and errors will be placed to `example1/bids/code/bidscoin/log/`
directory.

Apply nessesary modifications and rerun `bidsmapper.py` untill you don't 
see any warnings and/or errors. You don't need to add `-p example1/resources/plugins/bidsify_plugin.py` after first time, as plugin will be places into configuration file.

Alternatively, you can place already prepeared config file from `example1/resources/map`
to `example1/bids/code/bidscoin/`


Run bidsifier by executing
```
python $PATH/bidscoiner.py example1/renamed/ example1/bids
```

If everything is good, you will retrieve bidsified dataset in `example1/bids/`
