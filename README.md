# wikiedit-cogs
RED cogs for editing esports wikis

## Setup
Install it like a normal cog, with:
```
!repo add river https://github.com/RheingoldRiver/river-wiki-cogs
```

Then update with `!repo update river`

To setup bot password, send the following IN DM WITH THE BOT!!! NOT on a server!

```
!set api gamepedia account,RheingoldRiver bot,Nami password,sdfjklgsertgjselrgjsrtgh
```
Replace `RheingoldRiver` with your account name, `Nami` with the name of your bot password, and that keyspam with your actual bot password.
| Account | Bot | Password |
--- | --- | ---
| Actual name of Gamepedia account | Name you give the password at Special:BotPasswords | Password that gets generated for you |

It's suggested to use a unique bot password for this that you don't also use for another purpose (e.g. AWB, etc.)

There is one bot password per installation, so users will send edits as you when using these cogs.

## Development
You will need to install [esports-cog-utils](https://pypi.org/project/esports-cog-utils/):

```
pip install esports-cog-utils
```

Please try and keep all global Red-related dependencies there. Dependencies unrelated to Red may belong in [mwcleric](https://github.com/RheingoldRiver/mwcleric) or [mwrogue](https://github.com/RheingoldRiver/mwrogue) instead.