# Commane Line Interface

This module comes with a CLI interface to actually interact with your amplipi service via the webservice API.

This page tries to introduce the essentials of how this CLI is working, the full cocerage of what it can do for you should be explored by using the `--help` of the tool itself.

## Calling the script

The common installation of the module should introduce a local script alias that can be called:

```sh
$ pyamplipi --help
```

If that fails for some reason, one can resort to the standard python-module way to call:

```sh
$ python -m pyamplipi --help
```

## Grasping the command Layout 

The general command layout follows this pattern:

```sh
$ pyamplipi [general switches] TOPIC [COMMAND] [specific switches] [> output.json] [< input.json] 
```

* The `general switches` affect common settings about how to interact with your amplipi. Examples are the `-a AMPLIPI_API_URL` and the `-t AMPLIPI_TIMEOUT`.
* The `TOPIC` defines the entity or service on the amplipi with which you want to interact. Examples are `status`, `stream`, `announce`
* Most of these have various `COMMAND`s available. The most often recurring ones are:
    * `list` to produce a comprehensible overview listing of the `TOPIC`
    * `get «ID»` to read a json representation of the `TOPIC specified by ID` from the Amplipi service to stdout
    * `set «ID»` to write a json representation of the `TOPIC specified by ID` to the Amplipi service from stdin
* For some of these commands `specific switches` apply

Full listing and more explanation are offered by passing `-h` or `--help` either in the general or the specific switches.

Note that all switches have a `--Long` and a `-L` (short) variant

## Getting stdout Output

The `get` `COMMAND` generally will produce a json formatted output representation on stdout.

This allows to pipe the output to json handling tools (like `jq`) or simply redirect the output to a file using `> output-here.json`


## Reading Input 

The various `COMMAND`s that take input generally do that in two possible ways:


### (1) Input from stdin

Starting from a ready json file one can simply redirect that into the `set` `COMMAND`

```sh
# make the file
$ echo '{"media": "https://www.nasa.gov/mp3/640149main_Computers%20are%20in%20Control.mp3", "vol_f": 0.65, "source_id": 3}' > /tmp/my-announce.json

# pipe into script
$ cat /tmp/my-announce.json | pyamplipi -a http://amplipi.local/api/ -t 30 ann

# redirect into script
$ pyamplipi -a http://amplipi.local/api/ -t 30 ann < /tmp/my-announce.json
```

### (2) Input from CLI `--input [key=value]`

Alternatively the values can also be provided on the command line as key-value-pairs.

The equivalent of the above then becomes:

```sh
$ pyamplipi -a http://amplipi.local/api/ -t 30 ann -i media="https://www.nasa.gov/mp3/640149main_Computers%20are%20in%20Control.mp3" vol_f=0.65 source_id=3
```

**Note:** This second technique is only available for those TOPIC/COMMAND combinations where the input is simple enough to be provided using these key-value pairs.

One can use the `--help` to learn about the available keys for any specific TOPIC/COMMAND

```sh
$ pyamplipi ann --help
$ pyamplipi source set --help
```

## Using the environment

To shorten the amount of command line typing the values of most variables can be read from the environment.  Additionally a locally provided `.env` file can be used to provide these.  The included `dotenv.example` file shows the variables that can be set.

Again using the announcement example:

```sh
# create the .env file
$ echo 'AMPLIPI_API_URL=http://amplipi.local/api
AMPLIPI_TIMEOUT=30
AMPLIPI_ANNOUNCEMENT_MEDIA="https://www.nasa.gov/mp3/640149main_Computers%20are%20in%20Control.mp3"
AMPLIPI_ANNOUNCEMENT_VOL_F=0.65'  > .env

$ pyamplipi ann -i 
```

## Configure Logging

The CLI script uses python logging. It allows to provide an external yml configuration via `-l «config.yml»` that controls where various levels of logging need to be sent to.

The source code includes an example `debug-logconf.yml` for convenience.

**Tip:** Please make sure this config directs any output either to designated files, or to stderr so not to conflict with the json output (on stdout).

## Typical use cases

-- TODO provide some practical use cases

### Case 1 -- Making a status backup

```sh
$ pyamplipi status get > $(date --iso)-amplipi-status.json
```

### Case 2 -- Restoring  the latest status backup

 ```sh
 $ pyamplipi config load  < $(ls  -t1 *amplipi-status.json | head -1)  
```

Note:
* `config load` is actually an alias for `status set`
* `ls -t` sorts files newest to oldest, `ls -1` prints one per line, `| head -1` keeps the newest, and the construct `$(cmd)` puts the result of that into the line - effectively using the newest file matching the pattern as input

### Case 3 -- sed/awk away to increase the vol_f of a zone with 0.1