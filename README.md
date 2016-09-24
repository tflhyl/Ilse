## Ilse

Ilse is a command-line tool to interact with Lokalise's API.

### Installation

You can install Ilse using pip:

    pip install git+https://github.com/tflhyl/Ilse.git

Or you can clone this repo and build yourself. Ilse is written in Python 
and will require its dependencies to be installed
before you can use it:

    pip install -r requirements.txt

### Using Ilse

#### Configuration

Configuration parameters such as `API_TOKEN` are to be specified in the
`.ilseconfig` file. Take a look at `.ilseconfig.example` for an example
how it looks like.

Global parameters

| Params     | Remarks                                           |
| ---------- | ------------------------------------------------- |
| API_TOKEN  | A valid token that has access to the project.     |
| PROJECT_ID | The project ID. Go to project settings to get it. |

Resource parameters

| Params        | Remarks                                           |
| ------------- | ------------------------------------------------- |
| FORMAT        | The format of translation files. See supported formats [here](http://docs.lokali.se/en) |
| LANGUAGES     | The translation language ISO codes |
| FILES_DIR     | Path to the directory of translation files. Placeholder %LANG_ISO% will be replaced by the ISO code or anything defined in FILES_DIR_MAP |
| FILES_NAME    | The translation files name. Placeholder %FORMAT% will be replaced by the format specified in FORMAT |
| FILES_DIR_MAP | Mapping for language ISO codes to the custom or platform specific codes used in the directory path (e.g. zh_TW:zh-Hant)|

#### Pushing Translations

For a project in clean state, you probably need to push all the translation files:

    ilse push --replace

Note the `--replace` flag is needed because there's a bug in Lokalise that won't register the plurals translations on some platforms.

To push specific language (e.g. to update source language which needs translations):

    ilse push -l en [--replace]

`--replace` flag is optional. If it is not set, any updated values on existing keys will be ignored. 
However most of the time we do want to keep the translations on lokalise up to date with our local copies, 
so it is recommended to always use `--replace` flag. When we update some values on base language, we also 
want translators to re-translate them. Lokalise will mark updated keys as fuzzy to indicate this if we turn 
on **'Auto-toggle fuzzy'** option in the project settings.

You can use `--overwrite` flag to completely overwrite all the keys and values with the new uploaded files.
This is useful in case for example you delete some keys on your files and want it to be reflected on lokalise 
(without overwriting, the keys won't be deleted on lokalise).

#### Pulling Translations

To pull the translation files from Lokalise:

    ilse pull

The downloaded files will be automatically extracted to the correct directory and overwrite existing files. 

