# Insomnia bundle

This contains a useful [Insomnia V4](https://insomnia.rest/download/) 
YAML environment you can use to test HTTP endpoints out with.

To use it, you should set up the following variables in a PRIVATE environment 
(and make sure you do not push these ever!). All variables are strings

| Variable name         | Description                                                                                  |
|:----------------------|:---------------------------------------------------------------------------------------------|
| `authorization`       | An application's bot/bearer token, in the format `Bot xxxxxx`.                               |
| `client_id`           | An application's client ID snowflake.                                                        |
| `client_secret`       | An application's client secret.                                                              |

This should be provided in the following format:

```js
{
  "authorization": "...",
  "client_id": "...",
  "client_secret": "...",
  /* etc */
}
```
