Due April 15th
Harrison Wong (hcw29), Sherwin Li (sl855)

# Project Status

## What we do

We are working on the dropbox clone project. We are implementing a client that can encrypt and upload blocks to servers. The servers are running isis2 with the built in DHT for file storage. There may also be a web interface to the storage.

## How far we are / What remains to be done

We have written the client in python. It is about 300 lines of code of which the encryption and monitoring of a folder work. It maintains an internal database of the state of a folder, and encrypts blocks as necessary when they change. We need to implement uploading to the server and retrieving from the server.
The server is written using IronPython on C# with isis2. We made some modifications to the isis2 library to enable a different persistence method on the DHT. We store smaller metadata in memory, while we store larger data on disk. This is about 100 lines in C#. The python itself is about 200 lines of code that interacts with isis2. We need to implement saving creating a REST server to interact with the client as well as a few encryption/signing mechanisms to ensure that users cannot affect another's data.
We are considering re-implementing the DHT in isis2 to better suit our purposes. We are thinking of an Amazon Dynamo kind of implementation that auto-scales to the size of the server pool. We would also modify it such that the state transfer would be postponed when a new server joins instead of transferring state at join time. We are also considering enforcing stronger consistency by assigning a master to the data and using chain replication rather than the BASE approach.

## Timeline of future events

### Week 1

Get client and server connected to each other and working.

### Week 2

Ensure that encryption, signing work. Web page work.

### Week 3

Prepare presentation, reimplement DHT if enough time

## May 5 Project Demo

We plan to display our client running on multiple computers and our server running on multiple computers. We would also demonstrate our web page client that would allow users to connect remotely without the client installed. We would like to also give a rundown of the encryption features, consistency guarantees and the like. We feel that this is the real meat of the work.