Documentation
=============

.. toctree::
   :numbered:
   :maxdepth: 1


Introduction
==============


ITWS est une solution qui vous permet de créer rapidement un site internet.
Cette documentation a pour but de vous guider dans la prise en main et l'administration d'ITWS.


La Théorie: Prise en main des concepts ITWS
===================================================

Structuration de mon site
-------------------------

Ce croquis représente les différents éléments constituant votre site Internet:

.. figure:: figures/layout.*


Voici un tableau récapitulatif des différentes zones de votre site:

.. list-table::
    :header-rows: 1
    :widths: 100, 500

    * - Zone
      - Description de la zone*

    * - Haut de page
      - Le haut de page contient votre logo, votre slogan, un lien pour vous
        connecter, déconnecter ainsi qu'une zone de recherche

    * - Le menu
      - Le menu de votre site est le principal élément de navigation. Il est
        personnalisable facilement dans le panneau de contrôle.

    * - Zone de contenu
      - Il s'agit de la zone principale de votre site.

    * - Le fil d'arianne
      - Ce fil situé sous le menu vous permet de savoir où vous êtes sur le
        site et de revenir en arrière (dans la section qui contient la page que
        vous visualisez par exemple).

    * - Barre latérale
      - Votre site dispose d'une barre latérale qui va vous permettre de dynamiser votre site.

    * - Pied de page
      - Le pied de page vous permet d'ajouter des informations sur votre société/organisation.


Types de ressources
----------------------

Comme pour votre ordinateur, votre site internet est composé d'un ensemble de Dossiers et de Fichiers.
Dans ITWS on appelle cela des "ressources". Ces ressources sont présentes sous deux formes :

  - Les "Dossiers" qui peuvent contenir d'autres fichiers ou dossiers
  - Les "Fichiers" qui ne peuvent pas contenir d'autres ressources.

Voici la liste complète des ressources d'ITWS :


.. list-table::
    :header-rows: 1
    :widths: 30, 120, 350

    * - Logo
      - Type
      - Description

    * - .. image:: figures/html.*
      - Page Internet
      - Page Internet (article, etc.)

    * - .. image:: figures/file.*
      - Fichier
      - Vous pouvez ajouter dans votre site internet des fichiers pour les
        partager avec vos visiteurs. Il est ainsi possible d'ajouter tout type
        de fichiers (documents bureautiques, pdf, sons, etc.)

    * - .. image:: figures/image.*
      - Image
      - Image, photo, etc.

    * - .. image:: figures/image.*
      - RSSFeeds
      - Flux RSS

    * - .. image:: figures/tags.*
      - Tag
      - Marqueur lexical permettant de regrouper des ressources

    * - .. image:: figures/folder.*
      - Dossier
      - Conteneur utilisé pour classer des documents bureautiques par exemple.

    * - .. image:: figures/tracker48.*
      - Tracker (optionnel)
      - Outil de suivi par système de tickets, utilisé pour la gestion de projet.

    * - .. image:: figures/section.*
      - Section
      - Une section est un dossier dont la vue est configurable.

    * - .. image:: figures/news_folder.*
      - News
      - Actualité


Votre site internet met à votre disposition un "Navigateur" qui vous permet de parcourir l'ensemble
des dossiers et fichiers de votre site Internet.
Nous allons présenter le navigateur dans la section suivante.

Le navigateur
------------------------------------

Votre site Internet est composé d'un ensemble de dossiers et de fichiers
tout comme votre votre système d'exploitation préféré (Windows/Linux/Mac).

Un navigateur est accessible à tout moment depuis l'icône présente dans la
barre d'administration:

.. figure:: figures/admin_bar_manage-fr.*


Ce navigateur  vous permet de naviguer dans l'arborescence de votre site Internet :

.. figure:: figures/navigator-fr.*

Légende :

  1. Recherche plein-texte
  2. Filtre par type de contenu
  3. Lien pour visualiser la ressource
  4. Lien pour éditer la ressource
  5. Barre d'action sur la ou les ressources sélectionnées.



Les Barres d'administration
----------------------------

Lorsque vous êtes connecté en tant qu'Administrateur du site, une barre comme celle ci...

.. figure:: figures/admin_bar-fr.*

... apparaît en haut de votre site internet.
Celle-ci vous permet d'administrer facilement votre site.
Cette barre d'administration est composée de 3 blocs.

**Barre numéro 1**

.. figure:: figures/admin_bar_1-fr.*

La première barre d'administration, qui est toujours affichée vous permet::

   - D'accéder rapidement à la page d'accueil
   - D'accéder au panneau de contrôle dans lequel vous pouvez configurer votre site internet
   - D'accéder à l'interface d'ajout d'une nouvelle ressource

**Barre numéro 2**

.. figure:: figures/admin_bar_2-fr.*

La deuxième barre d'administration est la barre d'administration la plus importante.
Celle-ci est différente sur toutes les pages de votre site.

Cette barre vous donne des informations importantes :

    - Le type de la ressource courante (Section/WebPage...)
    - L'état de publication de la ressource (Vert=public, rouge=Privé, blanc=Pas de workflow)

Vous disposez aussi de boutons permettant d'agir sur la ressource courante.


**Barre numéro 3**

.. figure:: figures/admin_bar_3-fr.*

Cette troisième barre vous permet d'activer ou non le mode édition.

Si le mode édition est activé, des boutons d'actions suplémentaires seront affichés
lors de la navigation dans votre site.
Ces boutons permettent d'éditer votre site. (D'où le nom de "mode édition").

Si le mode édition est désactivé, les boutons d'actions supplémentaires seront cachés.


La barre d'administration centrale
-----------------------------------------------------------

Les 3 variantes de barre centrale
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La barre centrale varie en fonction du type de la ressource dans laquelle vous vous trouvez.
On peut néanmoins distinguer trois variantes de cette barre centrale :

  - La barre centrale du site Internet (à la racine du site)
  - La barre centrale de contenu de type "Contenant". Par exemple "Section" ou "Dossier"
  - La barre centrale sur du contenu éditable. Par exemple "Page Internet" ou "Fichier"

Nous allons présenter, ci-après, les 3 variantes de la barre centrale.

Barre d'administration de la racine de votre site
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lorsque vous êtes à la racine de votre site internet, vous devriez voir cette barre d'administration:

.. figure:: figures/admin_bar_2-fr.*

Le titre de la ressource courante est "ITWS Web Site", car vous êtes à la racine de votre site.

L'expression "ITWS Web Site" n'est pas colorée (en vert/orange/ou rouge) car le site est forcément public.

Cinq actions sont réalisables:

  - **Voir** permet de visualiser la page d'accueil de votre site
  - **Modifier** permet de modifier le titre, et l'apparence de la page d'accueil
  - **Configuration** permet d'accéder au panneau d'administration de votre site
  - **Icône Dossier** permet d'accéder au navigateur de fichiers de votre site.
  - **Icône Nouvelle ressource** permet d'ajouter une nouvelle ressource à la racine de votre site

Barre d'administration d'une Section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lorsque la ressource courante est une section, vous devriez voir cette barre d'administration

.. figure:: figures/admin_bar_section-fr.*

Le titre de la ressource courante est donc "Section".
Ce titre est coloré en vert car la ressource est publiée.

Cinq actions sont réalisables:

  - **Voir** permet de visualiser la section
  - **Modifier** permet de modifier le titre, et l'apparence de la section
  - **Avancé** permet d'effectuer des opérations avancées sur la section :
        - Voir l'historique de modification de la section
        - Voir la liste des liens et rétroliens de la section
        - Gérer la table des matières de la section
  - **Icône Dossier** permet d'ouvrir le navigateur de fichiers.
    Le navigateur sera ouvert à l'emplacement courant.
  - **Icône Nouvelle ressource** permet d'ajouter une nouvelle ressource dans la section courante


Barre d'administration d'une "Page Internet"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lorsque la ressource courante est une page internet, vous devriez voir cette barre d'administration :

.. figure:: figures/admin_bar_webpage-fr.*

Le titre de la ressource courante est donc "Page Web"
Ce titre est coloré en vert car la ressource est publiée.
Quatre actions sont réalisables :

    - **Voir** permet de visualiser la "Page Internet"
    - **Modifier** permet de modifier le contenu de la "Page Internet"
    - **Avancé** permet d'accéder à des actions avancées
    - **Icône Dossier parent** permet d'ouvrir le navigateur dans la section parente qui contient la ressource courante.


Les Sections
===========================

Une section est une ressource (de type dossier) dont la vue est configurable.
Il est possible de choisir le type d'affichage parmi ces 3 vues :

  - Vue composite
  - Vue galerie
  - Vue du flux

Certaines de ces vues sont configurables.
La configuration se réalise via le lien "Vue configuration" de la barre d'administration.


Vue composite
--------------------

La vue composite est composée d'un ensemble de blocs ordonnable.

.. figure:: figures/edit-composite-section.*

Description:

   - (1) On est bien sur une section
   - (2) Le mode édition est activé
   - (3) Il est possible d'ordonner et d'ajouter des boîtes dans la vue composite
   - (4) Un bouton permet de modifier chaque boîte de la vue composite

Voici le tableau des différents types d'éléments pouvant être ordonnés :

.. list-table::
    :header-rows: 1
    :widths: 30, 120, 350

    * - Logo
      - Type
      - Description

    * - .. image:: figures/html.*
      - Contenu
      - Zone de contenu html

    * - .. image:: figures/html.*
      - Contact
      - Formulaire de contact pour recueillir des messages des utilisateurs.

    * - .. image:: figures/html.*
      - Flux de contenu
      - Affiche un ensemble d'actualités (news), pages web et/ou sections d'un
        conteneur donné selon différents critères.

    * - .. image:: figures/html.*
      - Galerie
      - Galerie d'images, on affiche les miniatures des images.

    * - .. image:: figures/html.*
      - Carte
      - Affiche un emplacement sur Google Maps ou OpenStreetMap.

    * - .. image:: figures/html.*
      - Diaporama
      - Diaporama d'un ensemble d'images.


Vue galerie
--------------------

Galerie d'images.


Vue flux
--------------------

Cette vue permet d'afficher sur une page un ensemble d'actualités (news), pages
web et/ou sections d'un conteneur donné. Sont ici configurables le nombre
d'éléments affichés, le critère de tri, le gabarit d'affichage et un
sous-ensemble des mots clés définis (tags) sur lequel on pourra filtrer.


Configurer et administrer mon site Internet
=============================================

Se connecter en tant qu'Administrateur
---------------------------------------

Vous avez sans doute reçu, par email vos identifiant et mot de passe.
Si ce n'est pas le cas, demandez à l'administrateur du site de vous inscrire.

La première étape pour modifier votre site Internet est de vous identifier.
Vous pouvez vous identifier via le lien "Se connecter", situé en haut de la page.

Cette page va vous demander de saisir votre email et votre mot de passe.
Si vous avez oublié votre mot de passe, vous pouvez le réinitialiser en cochant la case "J'ai oublié mon mot de passe".





Le panneau de contrôle
-----------------------------

L'ensemble de la configuration de votre site Internet se réalise dans le panneau de contrôle de votre site Internet.

Lorsque vous êtes connecté en tant qu'administrateur, vous pouvez cliquer sur l'icône:

.. figure:: figures/control_panel.*

"Panneau de contrôle" de la première barre d'administration.

Voici une capture d'écran du panneau de contrôle:

.. figure:: figures/control_panel_view.*

A partir de ce panneau de contrôle vous pouvez :

  - Gérer les utilisateurs de votre site et leurs droits
  - Créer de nouveaux utilisateurs
  - Modifier la liste des hôtes virtuels
  - Configurer la politique de sécurité
  - Modifier la liste des langues disponibles et la langue par défaut
  - Modifier les options de contact
  - Modifier le thème et la feuille CSS du site
  - Modifier la page 404 du site (Page affichée quand un utilisateur essaye d'accèder à une page qui n'existe pas)
  - Modifier le fichier robots.txt
  - Gérer la liste des tags
  - Configurer des informations de référencement
  - Visualiser les liens cassés, les ressources orphelines et l'historique des modifications de votre site

Gestion du thème
--------------------------

Dans le thème, vous pouvez:

  - Changer le favicon, et le logo de votre site internet
  - Choisir la skin utilisée
  - Modifier la feuille de style du site (CSS)
  - Modifier le menu du site
  - Modifier le pied de page du site (footer)

Modifier le menu principal
~~~~~~~~~~~~~~~~~~~~~~~~~~

XXX

Modifier l'apparence du site
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Choix de la skin et CSS



Gérer le contenu de mon site
===============================

Ajouter du contenu
---------------------

Pour ajouter du contenu à votre site, il suffit de créer une nouvelle ressource.
Le menu est toujours disponible dans la barre d'administration.

.. figure:: figures/add-ressource.*

La liste des différents types de ressources disponibles sera alors affichée :

.. figure:: figures/type-ressources.*

Une fois le type de ressource séléctionné, le formulaire d'ajout est affiché :

.. figure:: figures/add-ressource-form.*

Ce formulaire contient des informations importantes :

  - (1) Le type de la ressource selectionnée
  - (2) La description du type de ressource selectionnée

Vous devez saisir deux champs :

 - (3) Le titre de la ressource. Ce champs est obligatoire.
 - (4) Vous devez sélectionner dans la liste déroulante, l'emplacement dans lequel vous voulez ajouter votre ressource.

Dans la zone texte, vous pouvez saisir le nom de la ressource.
Ceci n'est pas obligatoire, en effet si le nom n'est pas saisit, il sera calculé automatiquement à partir du titre saisit.
Exemple:

  - Titre              -> Nom
  - "Ma voiture bleue" -> "ma-voiture-bleue"




Ajouter une actualité
-------------------------------

L'ajout d'une nouvelle actualité est très simple.

.. figure:: figures/add-news.*

Voici les deux étapes :

  - (1) Cliquer sur le bouton "Ajouter une nouvelle ressource" du panneau d'administration
  - (2) Sélectionner la ressource de type "Actualité"


Editeur HTML
------------

TinyMCE


Les tags
------------

Un tag est un marqueur lexical utilisé pour regrouper des ressources ayant quelque chose en commun.
Par exemple vous pouvez regrouper des actualités parlant d'évènements se passant à Paris grâce au tag "Paris".
Une page internet sera alors automatiquement construite et regroupera tous les articles possédant ce tag.
L'URL de cette page sera du type :

  http://www.example.com/tags/paris

Il est possible d'associer des tags aux ressources de type :

  - Page Internet
  - Section

La liste des tags est administrable via l'onglet tags du panneau d'administration :

.. figure:: figures/tags.*

Depuis cette vue d'administration vous pouvez :

  - Ajouter dex nouveaux tags
  - Lister les tags existants
  - Publier ou dépublier des tags
  - Supprimer des tags
  - Afficher le nombre de ressources associées aux différents tags
  - Lister les ressources associées aux différents tags

Dans une page internet et dans une section, un selecteur de tag est disponible :

.. figure:: figures/selection-tags.*

Il vous suffit de sélectionner un tag et de cliquer sur le bouton ">" pour ajouter le tag à la page internet.
Le bouton "»" permet d'associer tous les tags à la page internet courante.



Exemple: création d'une galerie d'images
------------------------------------------

XXX




Les vues avancées
-----------------------------

Certaines ressources disposent de vues avancées

.. list-table::
    :header-rows: 1
    :widths: 100, 500

  * - Vue
    - Description

  * - Links
    - XXX

  * - Backlinks
    - XXX

  * - Commit log
    - XXX

  * - Subscriptions
    - XXX


Mon site et le référencement
==============================

ITWS est une solution naturellement optimisée pour le réferencement.

Dans cette partie de la documentation nous allons vous présenter
quelques actions qui vous permettront d'améliorer encore davantage votre
réferencement :


**Sitemap.xml** XXX
**Robots.txt** XXXX
**Vue SEO** XXX (Google key / Yahoo key /) Google Webmaster tools


Questions
=========

Voici les réponses aux questions fréquemment posées :

**Comment savoir si je dois ajouter une section ou une webpage ?**

XXX

**Comment ?**

XXX



Vocabulaire
===========

Voici des définitions de mots ou expressions que nous allons utiliser dans
cette documentation.

CMS
---

CMS signifie en anglais Content Management System (système de gestion de
contenu).

Une ressource
-------------

Dans ITWS, une ressource désigne à peu près tout type d'objet mis à la
disposition des utilisateurs.

Workflow
--------

Un workflow définit l'état d'une ressource et les transitions entre ces états
(privé, en attente de publication, publié).

SEO
----
Search Engine Optimization.


À propos
========

Cette documentation a été rédigée par:

   - Taverne Sylvain
   - Deram Nicolas
