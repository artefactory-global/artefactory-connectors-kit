# Nautilus Connectors Kit

**NCK is a Command-Line Interface (CLI), allowing you to easily request, stream and store raw reports, from the API source to the destination of your choice.**

The official documentation is available [here](https://artefactory.github.io/nautilus-connectors-kit/).

## Philosophy

The application is composed of **3 main components** (*implemented as Python classes*). When combined, these components act as data connectors, allowing you to stream data from a source to the destination of your choice:

- [Readers](nck/readers) are reading data from an API source, and transform it into a stream object.
- [Streams](nck/streams) (*transparent to the end-user*) are local objects used by writers to process individual records collected from the source.
- [Writers](nck/writers) are writing the output stream object to the destination of your choice.

## Available connectors

As of now, the application is offering:
 
### Readers

**Analytics**

- Adobe Analytics 1.4
- Adobe Analytics 2.0
- Google Analytics

**Advertising**

- **DSP**

    - Google Display & Video 360
    - The Trade Desk

- **Adserver**

    - Google Campaign Manager

- **Search**

    - Google Ads
    - Google Search Ads 360
    - Google Search Console
    - Yandex Campaign
    - Yandex Statistics

- **Social**

    - Facebook Marketing
    - MyTarget
    - Radarly
    - Twitter Ads

**CRM**

- SalesForce

**Databases**

- MySQL

**Files (.csv, .njson)**

- Amazon S3
- Google Cloud Storage
- Google Sheets

**DevTools**

- Confluence


### Writers

**Files (.njson)**

- Amazon S3
- Google Cloud Storage
- Local file

**Data Warehouse**

- Google BigQuery

**Debugging**

- Console

*A data connector could be, for instance, the combination of a Google Analytics reader + a Google Cloud Storage writer, collecting data from the Google Analytics API, and storing output stream records into a Google Cloud Storage bucket.*

For more information on how to use NCK, check out the [official documentation](https://artefactory.github.io/nautilus-connectors-kit/).
