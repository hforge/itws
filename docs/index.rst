Documentation
=============

.. toctree::
   :numbered:
   :maxdepth: 1



ITWS est une solution qui vous permet de créer rapidement un site internet.

Cette documentation a pour but de vous guider dans la prise en main et l'administration d'ITWS.

.. contents:: Menu


La Théorie: Prise en main des concepts ITWS
===================================================

Structuration de mon site
-------------------------

Ce croquis représente les différents éléments constituant votre site Internet:

.. figure:: figures/layout.*


Voici un tableau récapitulatif des différentes zones de votre site:

.. list-table:: Tableau
    :header-rows: 1
    :widths: 100, 500

    * - Zone
      - Description de la zone*

    * - Haut de page
      - Le haut de page contient votre logo, votre slogan, un lien pour vous connecter, déconnecter ainsi qu'une zone de recherche

    * - Le menu
      - Le menu de votre site est le principal élément de navigation. Il est personnalisable facilement dans le panneau de contrôle.

    * - Zone de contenu
      - XXX

    * - Le fil d'arianne
      - XXX

    * - Barre latérale
      - Votre site dispose d'une barre latérale qui va vous permettre de dynamiser votre site

    * - Pied de page
      - Le pied de page vous permet d'ajouter des informations sur votre société/organisation


Types de resources
----------------------

Comme pour votre ordinateur, votre site internet est composé d'un ensemble de Dossiers et de Fichiers.
Dans ITWS on appele cela des "Resources". Ces resources sont regroupables dans deux groupes:

  - Les "Dossiers" qui peuvent contenir d'autres fichiers ou dossiers
  - Les "Fichiers" qui ne peuvent pas contenir d'autres resources.

Voici la liste complétes des resources d'ITWS:


.. list-table:: Tableau
    :header-rows: 1
    :widths: 100, 200, 200

    * - Logo
      - Type
      - Description

    * - .. image:: figures/html.*
      - Page Internet
      - Page Internet

    * - .. image:: figures/file.*
      - Fichier
      - Vous pouvez ajouter dans votre site internet des fichiers pour les partager avec vos visiteurs. Il est ainsi possible d'ajouter tout type de fichiers

    * - .. image:: figures/image.*
      - Image
      - Description

    * - .. image:: figures/image.*
      - RSSFeeds
      - Description

    * - .. image:: figures/image.*
      - Tag
      - Description

    * - .. image:: figures/folder.*
      - Dossier
      - Description

    * - .. image:: figures/folder.*
      - Tracker
      - Description

    * - .. image:: figures/section.*
      - Section
      - Description

    * - .. image:: figures/section.*
      - News
      - Description


Votre site internet met à votre disposition un "Navigateur" qui vous permet de parcourir l'ensemble
des dossiers et fichiers de votre site Internet.
Nous allons présenter le navigateur dans la section suivante.

Le navigateur
------------------------------------

Votre site Internet est composé d'un ensemble de dossiers et de fichiers
tout comme votre votre système d'exploitation préféré (Windows/Linux/Mac).
Un navigateur est ainsi disponible dans votre site internet pour naviguer
dans l'arborescence de votre site:

.. figure:: figures/navigator.*

Le navigateur est accessible à tout moment depuis l'icône présent dans la
barre d'administration:

  XXX

A partir du navigateur, vous pouvez effectuer des actions,
sur une ou plusieurs resources à la fois:

  - Renommer
  - Supprimer
  - Copier
  - Coller
  - Publier
  - Dépublier




Les Barres d'administration
----------------------------

Lorsque vous êtes connecté en tant qu'Administrateur du site, une barre comme celle ci...

.. figure:: figures/admin_bar.*

... apparaît en haut de votre site internet.
Celle-ci vous permet d'administrer facilement votre site.
Cette barre d'administration est composée de 3 blocs.

**Barre numéro 1**

.. figure:: figures/admin_bar_1.*

La premiére barre d'administration, qui est toujours affichée vous permet::

   - D'accéder rapidement à la page d'accueil
   - D'accéder au panneau de contrôle dans lequel vous pouvez configurer votre site internet
   - D'accéder à l'interface d'ajout d'une nouvelle resource

**Barre numéro 2**

.. figure:: figures/admin_bar_2.*

La deuxiéme barre d'administration est la barre d'administration la plus importante.
Celle-ci est différentes sur toutes les pages de votre site.

Cette barre vous donne des informations importantes:

    - Le type de la resource courante (Section/WebPage...)
    - L'état de publication de la resource (Vert=public, rouge=Privé, blanc=Pas de workflow)

Vous disposez aussi de boutons permettant d'agir sur la resource courante.


**Barre numéro 3**

.. figure:: figures/admin_bar_3.*

Cette troisième barre vous permet d'activer ou non le mode édition.

Si le mode édition est activé, des boutons d'actions suplémentaires seront affichées
lors de la navigation dans votre site.
Ces boutons permettent d'éditer votre site. (D'où le nom de 'mode édition).

Si le mode édition est désactivé, les boutons d'actions supplémentaires seront cachés.


La barre d'administration centrale
-----------------------------------------------------------

Les 3 variantes de barre centrale
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La barre centrale varie en fonction du type de la resource dans laquelle vous vous trouvez.
On peut néanmoins distinguer trois variantes de cette barre centrale:

  - La barre centrale du site Internet (à la racine du site)
  - La barre centrale de contenu de type "Contenant". Par exemple "Section" ou "Dossier"
  - La barre centrale sur du contenu éditable. Par exemple "Page Internet" ou "Fichier"

Nous allons présenter, ci-aprés, les 3 variantes de la barre centrale.

Barre d'administration de la racine de votre Site
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lorsque vous êtes à la racine de votre site internet, vous devriez voir cette barre d'administration:

.. figure:: figures/admin_bar_2.*

Le titre de la resource courante est "ITWS Web Site", car vous êtes à la racine de votre site.

L'expression "ITWS Web Site" n'est pas colorée (en vert/orange/ou rouge) car le site est forcément public.

Cinq actions sont réalisables:

  - **Voir** Cela permet de visualiser la page d'accueil de votre site
  - **Modifier** Cela permet de modifier le titre, et l'apparence de la page d'accueil
  - **Configuration** Cela permet d'accèder au panneau d'administration de votre site
  - **Icône Dossier** Vous permet d'accèder au navigateur de fichier de votre site.
  - **Icône Nouvelle ressource** Vous permet d'ajouter une nouvelle resource à la racine de votre site

Barre d'administration d'une Section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lorsque la resource courante est une section, vous devriez voir cette barre d'administration

XXX

Le titre de la resource courante est donc "Section".
Ce titre est coloré en vert car la resource est publiée.

Cinq actions sont réalisables:

  - **Voir** Cela permet de visualiser la section
  - **Modifier** Cela permet de modifier le titre, et l'apparence de la section
  - **Avancé** Vous pouvez effectuer des opérations avancées sur la section:
        - Voir l'historique de modification de la section
        - Voir la liste des liens et rétroliens de la section
        - Gérer la table des matiéres de la section
  - **Icône Dossier** Vous permet d'ouvrir le navigateur de fichier.
    Le navigateur sera ouvert à l'emplacement courant.
  - **Icône Nouvelle ressource** Vous permet d'ajouter une nouvelle resource dans la section courante


Barre d'administration d'une "Page Internet"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lorsque la resource courante est une Page Internet, vous devriez voir cette barre d'administration:

XXX

Le titre de la resource courante est donc "Page Web"
Ce titre est coloré en vert car la resource est publiée.
Quatres actions sont réalisables:

    - **Voir** Cela permet de visualiser la "Page Internet"
    - **Modifier** Cela permet de modifier le contenu de la "Page Internet"
    - **Avancé** Qui permet d'accéder à des actions avancées
    - **Icône Dossier parent** Vous permet d'ouvrir le navigateur dans la section parente qui contient la resource courante.



Configurer et administrer mon site Internet
=============================================

Se connecter en tant qu'Administrateur
---------------------------------------

Vous avez sans doute reçu, par email vos identifiants et mot de passe.
Si ce n'est pas le cas, demandez à l'administrateur du site de vous inscrire.

La première étape pour modifier votre site Internet est de vous identifier.
Vous pouvez vous identifier via le lien "Se connecter", présentant en haut de page.

Cette page va vous demander de saisir votre email et votre mot de passe.
Si vous avez oublié votre mot de passe, vous pouvez le réinitialiser en cochant la case "J'ai oublié mon mot de passe".





Le panneau de contrôle
-----------------------------

L'ensemble de la configuration de votre site Internet ce réalise dans le panneau de contrôle de votre site Internet.

Lorsque vous êtes connecté en tant qu'administrateur, vous pouvez cliquer sur l'icône:

.. figure:: figures/control_panel.*

"Panneau de contrôle" de la premiére barre d'administration.

Voici une capture d'écran du panneau de contrôle:

.. figure:: figures/control_panel_view.*

A partir de ce panneau de contrôle vous pouvez:

  - Gérer les utilisateurs de votre site et leurs droits
  - Créer de nouveaux utilisateurs
  - Modifier la liste des Hôtes virtuels
  - Configurer la politique de sécurité
  - Modifier la liste des langues disponibles et la langue par défaut
  - Modifier les options de contact
  - Modifier le thème et la feuille CSS du site
  - Modifier la page 404 du site (Page affichée quand un utilisateur essaye d'accèder à une page qui n'existe pas)
  - Modifier le fichier robots.txt
  - Gérer la liste des tags
  - Configurer des informations de référencement
  - Visualiser les liens cassés, les resources orphelines et l'historique des modifications de votre site

Gestion du thème
--------------------------

Dans le thème, vous pouvez:

  - Changer le favicon, et le logo de votre site internet
  - Choisir la skin utilisée
  - Modifier la feuille CSS du site
  - Modifier le menu du site
  - Modifier le footer du site

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

Folder / Section
Une section est

Editeur HTML
------------

TynyMCE


Les tags
------------

XXX


Exemple: création d'une gallerie d'images
------------------------------------------

XXX




Les vues avancées
-----------------------------

Certaines resources disposent de vues avancées

.. list-table:: Tableau
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


Mon site et le référemencement
==============================

ITWS est une solution naturellement optimisée pour le réferencement.

Dans cette partie de la documentation nous aller vous présenter
quelques actions qui vous permettrons d'améliorer encore XXX



**Sitemap.xml** XXX
**Tobots.txt** XXXX
**Vue SEO** XXX (Google key / Yahoo key /) Google Webmaster tools


Questions
=========

Voici les réponses aux questions fréquemment possées:

**Comment savoir si je doit ajouter une section ou une webpage ?**

XXX

**Comment ?**

XXX



Vocabulaire
===========

Voici des définitions de mots ou expressions que nous allons utiliser dans
cette documentation.

CMS
---

CMS signifie en anglais Content Management System.

Une resource
-------------

Dans ITWS, une resource

Workflow
--------

Un workflow



À propos
========

Cette documentation a été rédigée par:

   - Taverne Sylvain
   - XXX
