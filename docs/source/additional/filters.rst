.. _filters:

*****************
Filters Explained
*****************

<<<<<<< HEAD
So far, there has been a lot of talk about objects, filters, and alignment, but these can be a difficult-to-grasp concepts. These illustrated examples might be helpful in gleaning a better understanding of what is meant by "object", "filter" and "alignment".

The easiest way to start is with an example. Let's say the user wanted to search for **word-final fricatives in utterance-initial words**

While to a person this seems like a fairly simple tast that can be accomplished at a glance, for SCT it has to be broken up into its constituent steps. Let's see how this works on this sample sentence: 
=======
So far, there has been a lot of talk about filters and alignment, but these can be a difficult-to-grasp concepts. These illustrated examples might be helpful in gleaning a better understanding of what is meant by "filter" and "alignment".

Let's begin with a sample sentence. It has been split into the utterance (the whole sentence), words, and phones (for this example, the orthographic letters). 

>>>>>>> MontrealCorpusTools/master
	.. image:: fullsentence.png
		:width: 760px
		:height: 200px
		:align: center
		:alt: Image cannot be displayed in your browser
<<<<<<< HEAD
Here, each level (utterance, word, phone) corresponds to an object. Since we are ultimately looking for fricatives, we would want to select "phones" as our linguistic object to find. 

Right now we have all phones selected, since we haven't added any filters. Let's limit these phones by adding the first part of our desired query: word-final phones. To accomplish this, we need to grasp the idea of alignment. 

Each object (utterances, words, phones) has two boundaries, left and right. These are represented by the walls of the boxes containing each object in the picture. To be "aligned", two objects must share a boundary. For example, the non-opaque objects in the next 2 figures are all aligned. Shared boundaries are indicated by thick black lines. Parent objects (for example, words in which a target phone is found) are outlined in dashed lines. In the first picture, the words and phones are "left aligned" with the utterance (their left boundaries are the same as that of the utterance) and in the second image, words and phones are "right aligned" with the utterance. 
=======

Each object (utterances, words, phones) has two boundaries, left and right. These are represented by the walls of the boxes containing each object in the picture. To be "aligned", two objects must share a boundary. For example, the non-opaque objects in the next 2 figures are all aligned. Shared boundaries are indicated by thick black lines.
>>>>>>> MontrealCorpusTools/master

	.. image:: ex1.png
		:width: 760px
		:height: 200px
		:align: center
		:alt: Image cannot be displayed in your browser


	.. image:: ex2.png
		:width: 760px
		:height: 200px
		:align: center
		:alt: Image cannot be displayed in your browser

<<<<<<< HEAD
Now that we understand alignment, we can use it to filter for **word-final** phones, by adding in this filter:

	.. image:: ex3filt1.png
		:width: 566px
		:height: 132px
		:align: center
		:alt: Image cannot be displayed in your browser

By specifying that we only want phones which share a right boundary with a word, we are getting all **word-final** phones.

	.. image:: ex5.png
=======
In fact, we can say that in the first picture, the words and phones are "left aligned" with the utterance (their left boundaries are the same as that of the utterance) and in the second image, words and phones are "right aligned" with the utterance. 

Sometimes, we want to select different boundaries for different levels of objects. For example, in the following figure, we are selecting the word that is "left aligned" with the utterance, but the phone that is "right aligned" with that word. 

	.. image:: ex3.png
>>>>>>> MontrealCorpusTools/master
		:width: 760px
		:height: 200px
		:align: center
		:alt: Image cannot be displayed in your browser

<<<<<<< HEAD
However, recall that our query asked for **word-final fricatives**, and not all phones. This can easily be remedied by adding another filter \*:

	.. image:: fricativefilter.png
		:width: 616px
		:height: 150px
		:align: center
		:alt: Image cannot be displayed in your browser

\* **NB** the "fricative" property is only availably through `enrichment <http://sct.readthedocs.io/en/latest/additional/enrichment.html>`_

Now the following phones are found:


	.. image:: ex6.png
		:width: 760px
		:height: 200px
		:align: center
		:alt: Image cannot be displayed in your browser

Finally, in our query we wanted to specify only **utterance-intial** words. This will again be done with alignment. Since English reads left to right, the first word in an utterance will be the leftmost word, or the word which shares its leftmost boundary with the utterance. To get this, we add the filter: 

	.. image:: finalfilter.png 
		:width: 609px
		:height: 204px
=======
This is a good time to show how these examples translate into filters. 
For the first two examples, the filters would be quite simple.
	
	.. image:: ex1filt1.png
		:width: 727px
		:height: 187px
		:align: center
		:alt: Image cannot be displayed in your browser

	.. image:: ex1filt2.png
		:width: 727px
		:height: 187px
		:align: center
		:alt: Image cannot be displayed in your browser


We are looking for the smallest object (phones) and want to specify that their alignment is right/left with the object one level up (words). Then we also want to specify that the words should be right/left aligned with the level above them (utterances). This gives us all utterance-initial phones -- since the phones are word-initial and the words are utterance-initial. 

 For the third example, we only need to alter the filters slightly. We are still looking for utterance-intial words, so that filter does not change. However, we will change the first filter to make the phones right-aligned with words. This way we are getting word-final phones of utterance-intial words. 

 	.. image:: ex1filt3.png
		:width: 727px
		:height: 187px
		:align: center
		:alt: Image cannot be displayed in your browser

What if we wanted the final segment of the second word in an utterance? 

	.. image:: ex4.png
		:width: 760px
		:height: 200px
>>>>>>> MontrealCorpusTools/master
		:align: center
		:alt: Image cannot be displayed in your browser


<<<<<<< HEAD

This gives us the result we are looking for: **word-final fricatives in utterance-initial words**


	.. image:: ex3.png
=======
This is where the "following" and "previous" options come into play. We can use "previous" to specify the object before the one we are looking for. If we wanted the last phone of the second word in our sample utterance (the "s" in "reasons") we would want to specify something about the previous word's alignment. If we wanted to get the final phone of the words in this position, our filters would be: 

	.. image:: ex2filt1.png
		:width: 760px
		:height: 200px
		:align: center
		:alt: Image cannot be displayed in your browser


In all these examples, we only end up with one phone per utterance. However, this is certainly not always the case. For example, say we wanted every word-final phone. In this case, we no longer care about word alignment in the utterance, but we do care about phone alignment in the word. We would strip away our second filter. 
	
	.. image:: ex3filt1.png
>>>>>>> MontrealCorpusTools/master
		:width: 760px
		:height: 200px
		:align: center
		:alt: Image cannot be displayed in your browser

<<<<<<< HEAD


Another thing we can do is specify previous and following words/phones and their properties. For example: what if we wanted the final segment of the second word in an utterance? 

	.. image:: ex4.png
=======
As you can see, the fewer filters we have, the larger our set of results becomes. Recall that when we had no filters, all of the words and phones were in the set of results. 

	.. image:: ex5.png
		:width: 760px
		:height: 200px
		:align: center
		:alt: Image cannot be displayed in your browser

We can narrow our results by specifiying a subset of these phones we want. Say we had enriched the corpus earlier and encoded which segments are fricatives. We could get the following result

	.. image:: ex6.png
>>>>>>> MontrealCorpusTools/master
		:width: 760px
		:height: 200px
		:align: center
		:alt: Image cannot be displayed in your browser

<<<<<<< HEAD

This is where the "following" and "previous" options come into play. We can use "previous" to specify the object before the one we are looking for. If we wanted the last phone of the second word in our sample utterance (the "s" in "reasons") we would want to specify something about the previous word's alignment. If we wanted to get the final phone of the words in this position, our filters would be: 

	.. image:: ex2filt1.png
		:width: 645px
		:height: 135px
=======
by using these filters:

	.. image:: ex4filt1.png
		:width: 760px
		:height: 200px
>>>>>>> MontrealCorpusTools/master
		:align: center
		:alt: Image cannot be displayed in your browser




<<<<<<< HEAD
For a full list of filters and their uses, see the section on `building queries <http://sct.readthedocs.io/en/latest/additional/buildingqueries.html>`_
=======


>>>>>>> MontrealCorpusTools/master

