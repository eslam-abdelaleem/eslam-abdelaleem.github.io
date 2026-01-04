---
layout: page
title: Projects
permalink: /projects/
description: A selection of my research and open-source software.
nav: true
nav_order: 4
display_categories: [research, software]
horizontal: false
---

<div class="projects">
{% if site.enable_project_categories and page.display_categories %}
  {% for category in page.display_categories %}
  <h2 class="category">{{ category }}</h2>
  {% assign categorized_projects = site.projects | where: "category", category %}
  <div class="container">
    <div class="row row-cols-1 row-cols-md-2"> {% for project in categorized_projects %}
        {% include projects.liquid %}
      {% endfor %}
    </div>
  </div>
  {% endfor %}

{% else %}
  {% assign projects = site.projects | sort: "importance" %}
  <div class="row row-cols-1 row-cols-md-3">
    {% for project in projects %}
      {% include projects.liquid %}
    {% endfor %}
  </div>
{% endif %}
</div>
