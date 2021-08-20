Find collection dates: https://my.portsmouth.gov.uk/en/AchieveForms/?form_uri=sandbox-publish://AF-Process-26e27e70-f771-47b1-a34d-af276075cede/AF-Stage-cd7cc291-2e59-42cc-8c3f-1f93e132a2c9/definition.json

UPRN's: https://www.gov.uk/government/publications/open-standards-for-government/identifying-property-and-street-information

Usage:  
 `./pcc_bin_dates.py <postcode> [<filter>] [exact]`  
 *postcode* - The postcode to search for  
 *filter* (optional) - Used to filter down to a single address, if the filter matches multiple entries all entries will be listed and the filter will need to be made more specific  
 *exact* (optional) - Just the word 'exact', if it's the 3rd argument then the filter is used as an exact match for an address. Not always needed, but some addresses (for example number 1) could match multiple address on a street (from same example, numbers 11, 21, 31, etc) so a partial match would just list addresses rather than collection dates  
If filter is not included all addresses at the postcode are listed.  
I ususally just use my house number for the filter  

If there are multiple addresses available then a list of addresses is output, if a single address is found then bin collection dates for general rubbish and recycling is returned in JSON format.

Example (not an actual address, just an example of how it could be used):  
 List all addresses: `./pcc_bin_dates.py "PO1 1AA"`  
 Output collection dates: `./pcc_bin_dates.py "PO1 1AA" 73`  


Note: It can be a little slow to retrieve dates because PCC website is slow
