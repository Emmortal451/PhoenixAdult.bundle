import PAsearchSites
import PAgenres
import PAactors
import PAutils


def search(results,encodedTitle,title,searchTitle,siteNum,lang,searchDate):
    url = PAsearchSites.getSearchSearchURL(siteNum) + encodedTitle.replace('%20', '+')
    searchResults = HTML.ElementFromURL(url)
    for searchResult in searchResults.xpath('//div[contains(@class, "item-video")]'):
        titleNoFormatting = searchResult.xpath('.//a/@title')[0]
        curID = PAutils.Encode(searchResult.xpath('.//a/@href')[0])
        date = searchResult.xpath('.//div[@class="more-info-div"]')[0].text_content().split('|')
        releaseDate = parse(date[-1].strip()).strftime('%Y-%m-%d')

        if searchDate:
            score = 100 - Util.LevenshteinDistance(searchDate, releaseDate)
        else:
            score = 100 - Util.LevenshteinDistance(searchTitle.lower(), titleNoFormatting.lower())

        results.Append(MetadataSearchResult(id='%s|%d' % (curID, siteNum), name='%s [InterracialPass] %s' % (titleNoFormatting, releaseDate), score=score, lang=lang))

    return results


def update(metadata,siteID,movieGenres,movieActors):
    Log('******UPDATE CALLED*******')

    metadata_id = metadata.id.split('|')
    url = PAutils.Decode(metadata_id[0])
    detailsPageElements = HTML.ElementFromURL(url)

    # Studio
    metadata.studio = 'Interracial Pass'

    # Title
    metadata.title = detailsPageElements.xpath('//h2[@class="section-title"]')[0].text_content().strip()

    # Summary
    metadata.summary = detailsPageElements.xpath('//div[@class="update-info-block"]')[1].text_content().replace('Description:', '', 1).strip()

    # Tagline and Collection(s)
    metadata.collections.clear()
    tagline = PAsearchSites.getSearchSiteName(siteID).strip()
    metadata.tagline = tagline
    metadata.collections.add(tagline)

    # Genres
    movieGenres.clearGenres()
    for genreLink in detailsPageElements.xpath('//ul[@class="tags"]//li//a'):
        genreName = genreLink.text_content().strip()

        movieGenres.addGenre(genreName)

    # Release Date
    date = detailsPageElements.xpath('//div[@class="update-info-row"]')[0].text_content().replace('Released:', '', 1).strip()
    if date:
        date_object = parse(date)
        metadata.originally_available_at = date_object
        metadata.year = metadata.originally_available_at.year

    # Actors
    movieActors.clearActors()
    for actorLink in detailsPageElements.xpath('//div[contains(@class, "models-list-thumbs")]//li'):
        actorName = actorLink.xpath('.//span/text()')[0]
        actorPhotoURL = actorLink.xpath('.//img//@src0_3x')[0]
        if not actorPhotoURL.startswith('http'):
            actorPhotoURL = PAsearchSites.getSearchBaseURL(siteID) + actorPhotoURL

        movieActors.addActor(actorName, actorPhotoURL)

    # Posters
    art = []
    xpaths = [
        '//div[@class="player-thumb"]//img/@src0_1x'
    ]

    for xpath in xpaths:
        for img in detailsPageElements.xpath(xpath):
            if not img.startswith('http'):
                img = PAsearchSites.getSearchBaseURL(siteID) + img
            art.append(img)

    Log('Artwork found: %d' % len(art))
    for idx, posterUrl in enumerate(art, 1):
        if not PAsearchSites.posterAlreadyExists(posterUrl, metadata):
            # Download image file for analysis
            try:
                img_file = urllib.urlopen(posterUrl)
                im = StringIO(img_file.read())
                resized_image = Image.open(im)
                width, height = resized_image.size
                # Add the image proxy items to the collection
                if width > 1:
                    # Item is a poster
                    metadata.posters[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': 'http://www.google.com'}).content, sort_order=idx)
                if width > 100:
                    # Item is an art item
                    metadata.art[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': 'http://www.google.com'}).content, sort_order=idx)
            except:
                pass

    return metadata
