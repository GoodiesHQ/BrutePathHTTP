# BrutePathHTTP

Simple tool for brute forcing file paths in the HTTP protocol.

### Requirements
 - Python3.5+ supporting `async/await` syntax
 - `aiohttp`


### Setup
    git clone https://github.com/GoodiesHQ/BrutePathHTTP
    sudo python3 -m pip install -U virtualenv
    python3 -m virtualenv BrutePathHTTP
    cd BrutePathHTTP
    source ./bin/activate
    pip install -r requirements.txt
    pip install -r optional-requirements.txt
    
### Usage
|Flag|Alias|Multi|Default|Help|
|----|-----|-----|-------|----|
|--dir|-d|N|**Required**|Full path to HTTP directory.|
|--wordlist|-w|N|**Required**|File containing words to try.|
|--ext|-e|Y|[""]|List of extensions to attempt|
|--status|-s|Y|[200]|Status codes to accept.|
|--output|-o|N|"output.txt"|Output file to store discovered URLs|
|--conns|-c|N|100|Number of concurrent asynchronous connections.|
|--timeout|-t|N|10|Connection timeout (in seconds)|
|--verbose|-b|N|False|Verbose output|

#### Example:
    python3 brute_path_http.py -d http://example.com/dir/ -w words.txt -e php txt html -c 250
