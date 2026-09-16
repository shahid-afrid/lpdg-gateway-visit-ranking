# AI Usage

I used an AI coding assistant to help me understand the challenge brief and FAQs, discuss the project structure and analysis approach, and draft or review parts of the code and documentation.

I ran the solution locally, checked the generated predictions with the supplied validator, and tested the project in a clean environment. The supplied dataset remained local and was not uploaded to an external service.

## One issue found during testing

An AI-suggested data-handling step tried to fill both numeric and text columns with zero. The full historical run failed because the text column could not accept a numeric value. I changed the ranking code to fill numeric and text fields separately. The silent-gateway regression test checks those type-specific defaults.
