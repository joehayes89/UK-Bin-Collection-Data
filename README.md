### Python Script to scrape NEDDC website for bin collection data ###

Requires a selenium grid server to scrape the site

Replace the values in the constants.py file

You need to create two sensors in home assistant
 - sensor.next_bin_collection
 - sensor.bin_colour

Can either be triggered via a cron-job or by creating an automation to call a shell_command
````
shell_command:
  update_bin_data: 'python3 /config/python_scripts/bin_collection.py'
````

Example card using html template card:
(https://github.com/PiotrMachowski/Home-Assistant-Lovelace-HTML-Jinja2-Template-card)
Put assets folder in www/community/

````
type: custom:html-template-card
title: Next Bin Collection
ignore_line_breaks: true
entities: sensor.next_bin_collection
content: >
  {% set next_collection_date_str = states('sensor.next_bin_collection') %} {%
  set next_collection_date = strptime(next_collection_date_str, '%d/%m/%Y') %}

  <table style="width:100%; border-collapse: collapse;">
      <tr>
        <td rowspan="3" style="text-align:center; vertical-align:middle;">
          {% if 'Burgundy Bin' in states('sensor.bin_colour') %}
            <img src="/hacsfiles/assets/red.png" alt="Red bin" height="100"><br> Red Bin
          {% endif %}
          {% if 'Black Bin' in states('sensor.bin_colour') %}
            <img src="/hacsfiles/assets/black.png" alt="Black bin" height="100"><br> Black Bin
          {% endif %}
          {% if 'Green Bin' in states('sensor.bin_colour') %}
            <img src="/hacsfiles/assets/green.png" alt="Green bin" height="100"><br> Green Bin
          {% endif %}
          {% if 'Burgundy & Green Bins' in states('sensor.bin_colour') %}
            <img src="/hacsfiles/assets/red_green.png" alt="Red and Green bins" height="100"><br> Red and Green Bins
          {% endif %}
        </td>
      </tr>
      <tr>
        <td style="vertical-align:middle; text-align:center;">
          {{ as_datetime(next_collection_date).strftime('%A') }}
        </td>
      </tr>
      <tr>
        <td style="vertical-align:top; text-align:center;">
          {{ next_collection_date_str }}
        </td>
      </tr>
    </table>
````
