

def compute_nav(home_url, view, timeframe, recent_authors):
    return ''.join(
        ['<li><a href="{home_url}{view}{timeframe}{name_ref}/">{name}</a></li>'.format(
            name=author, name_ref=author.replace(' ', '_'), home_url=home_url,
            timeframe=timeframe, view=view)
            for author in recent_authors])
