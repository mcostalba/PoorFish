---
layout: default
title: Archive
scripts: [search.js]
permalink: /archive
---
<div class="archive-header">
    <h2>Archives</h2>
    <span class="icon toggle-search">{% include search.svg %} Search</span>
</div>
<div class="search">
    <div class="wrapper">
        <span class="icon toggle-search">{% include close.svg %}</span>
        <input type="text" class="search-input" id="search-input" placeholder="Search...">
        <ul id="results-container"></ul>
    </div>
</div>
<ul class="archive-lists">
  {% for post in site.posts %}
    {% unless post.next %}
      <div class="by-year">
        <h3>{{ post.date | date: '%Y' }}</h3>
    {% else %}
      {% capture year %}{{ post.date | date: '%Y' }}{% endcapture %}
      {% capture nyear %}{{ post.next.date | date: '%Y' }}{% endcapture %}
      {% if year != nyear %}
      </div>
      <div class="by-year">
        <h3>{{ post.date | date: '%Y' }}</h3>
      {% endif %}
    {% endunless %}
    <li><span class="date">{{ post.date | date:"%b" }}</span> <a href="{{ post.url | prepend: site.baseurl }}">{{ post.title }}</a></li>
  {% endfor %}
</div></ul>
<span class="last-update">Site last generated: {{ site.time | date: "%b %-d, %Y"  }}</span>
