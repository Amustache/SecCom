# SecCom

Projet de visualisation de données géographiques longitudinales.


# Documentation 

## Description du projet: 

Ce projet explore diverses techniques pour la visualisation interactive et longitudinale des résultats d'enquêtes en Suisse. Le but est de fournir un outil permettant de naviguer à travers les questions d'enquête et de les regrouper en questions globales à travers les années, avec une interface adaptée aux utilisateurs multilingues et accessible à tous.

## Visualisation interactive 

La partie visualisation du projet a été développée en utilisant une interface Dash/Plotly intégrée à une application Flask. Ce choix a été motivé par le côté interactif de Dash/Plotly, qui permet de créer des graphiques dynamiques et réactifs, offrant une expérience utilisateur fluide. Les utilisateurs peuvent ajuster des filtres, tels que les années ou le choix entre les questions globales et les enquêtes spécifiques.

Les années sélectionnables sont : 1988, 1994, 1998, 2005, 2009, 2017 et 2023, avec 2023 comme valeur par défaut.

## Rassemblement des questions globales à travers les enquêtes

Afin d'automatiser la détection et le regroupement des questions similaires à travers les années en questions globales, une approche NLP (Natural Language Processing) a été mise en place.

Techniques testées :

    Prétraitement du texte :
        Suppression des stopwords.
        Suppression de la ponctuation.
        Lemmatisation pour réduire les mots à leur forme racine.

    Modèles testés :
        BERT : Un modèle de transformer puissant a été testé avec deux variantes :
            Couplé à une matrice de similarité pour détecter des similitudes textuelles.
            Utilisé avec DBSCAN pour le regroupement des questions par clusters basés sur la densité.

Bien que prometteurs, ces modèles n'ont pas produit de résultats suffisamment satisfaisants. 

## Méthode retenue : TF-IDF

Finalement, nous avons opté pour une méthode plus simple, mais efficace, le TF-IDF (Term Frequency - Inverse Document Frequency). TF-IDF permet de quantifier l'importance d'un mot dans un texte en fonction de sa fréquence dans un document et à travers plusieurs documents. En bref, il pondère l'importance des termes rares mais significatifs dans le texte.

Approches utilisées pour classer les questions globales :

    Seuil (Threshold) : Une première approche consistait à regrouper les questions globales en fonction d'un seuil de similarité.
    Top 10 : Une seconde méthode était basée sur un "top 10" des questions les plus globales, calculées via les résultats du TF-IDF.

Les résultats obtenus à partir de ces méthodes ont été utilisés en entrée pour la partie projection cartographique.

## Traductions multilingues

Le projet étant destiné à une utilisation en Suisse, où quatre langues officielles sont parlées (allemand, français, italien, romanche), il a été jugé pertinent de rendre l'application disponible dans ces langues. Nous avons implémenté un système de traduction local, sans avoir recours à des API externes, pour garantir la confidentialité des données.

Tests et approches :

    LibreTranslate : Un premier test avec cet outil open-source a été réalisé mais les résultats n'étaient pas concluants.
    MBART de Facebook : Nous avons ensuite testé des modèles de transformers, et le modèle MBART a montré les meilleurs résultats pour les traductions multilingues. Il a donc été adopté pour le projet.

Malheureusement, le romanche n'est pas disponible à la traduction depuis ces librairies. 

## Accessibilité

Pour s'assurer que la visualisation est accessible à tous, une palette de couleurs spécialement adaptée aux personnes souffrant de troubles de la vision des couleurs a été implémentée. Cela permet une lecture plus facile et inclusive des graphiques.


## Crédits

- Matthieu Jacques
