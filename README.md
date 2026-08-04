The code included in this repository was used to support the paper submitted for the proceedings of the XAFS 2026 conference.

The three notebooks included are intended to show:

- How to add provenance a Galaxy RO-Crate (RO_Crate_Processing.ipynb).
- How to extract interoperability and discovery metadata from the RO-Crate (using the CDIF-4-XAS model) (Read Modified RO-Crate.ipynb).
- How to use the interoperability metadata to extract and use the data in the RO-Crate outside Galaxy (Use RO-Crate Datasets.ipynb)

Most of the processing (extracting provenance and modifying RO-Crate) is stored in read_provenance.py, the functions to process data are in lin/larch_data_reader.py, while the plotting functions are in lib/custom_plots.py

# Funding
This work has been supported came from the following sources.

- UK Catalysis Hub is kindly thanked for resources and support provided via our membership of the UK Catalysis Hub Consortium and funded by EPSRC grant: UKRI945. 
- Additional the collaboration in the Physical Sciences Data Infrastructure (PSDI project) has also provided funding through EPSRC grants: EP/X032701/1, EP/X032663/1, and EP/W032252/1.
- This project also received funding from the European Union’s Horizon Europe research and innovation programme under grant agreement No 101129751 Open Science Clusters’ Action for Research and Society (OSCARS)-CDIF-4-XAS. 
