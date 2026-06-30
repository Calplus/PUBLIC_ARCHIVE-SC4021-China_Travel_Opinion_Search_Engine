# Sourced from Calplus (https://github.com/Calplus)
-- Server-side category assignment for ig_comments
-- Run in Supabase SQL Editor (no Python / no network overhead)
-- Estimated time: ig_posts/ig_comments ~30s, pinterest_pins ~5-15min

UPDATE instagram_crawl.ig_comments AS tbl
SET categories = computed.cats
FROM (
    SELECT id,
        ARRAY_REMOVE(ARRAY[
            CASE WHEN (t ~ $wb$\ytemple\y$wb$
                OR t ~ $wb$\ypalace\y$wb$
                OR t ~ $wb$\yancient\y$wb$
                OR t ~ $wb$\ydynasty\y$wb$
                OR t ~ $wb$\ywall\y$wb$
                OR t ~ $wb$\ypagoda\y$wb$
                OR t ~ $wb$\yshrine\y$wb$
                OR t ~ $wb$\ymosque\y$wb$
                OR t ~ $wb$\yruins\y$wb$
                OR t ~ $wb$\yunesco\y$wb$
                OR t LIKE '%forbidden city%'
                OR t LIKE '%great wall%'
                OR t ~ $wb$\yterracotta\y$wb$
                OR t ~ $wb$\ytomb\y$wb$
                OR t ~ $wb$\ymausoleum\y$wb$
                OR t ~ $wb$\yhutong\y$wb$
                OR t ~ $wb$\ycourtyard\y$wb$
                OR t ~ $wb$\ypavilion\y$wb$
                OR t ~ $wb$\yfortress\y$wb$
                OR t ~ $wb$\yimperial\y$wb$
                OR t ~ $wb$\yming\y$wb$
                OR t ~ $wb$\yqing\y$wb$
                OR t ~ $wb$\ytang\y$wb$
                OR t LIKE '%han dynasty%'
                OR t LIKE '%old town%'
                OR t LIKE '%ancient town%'
                OR t LIKE '%ancient city%'
                OR t LIKE '%city wall%'
                OR t LIKE '%drum tower%'
                OR t LIKE '%bell tower%'
                OR t LIKE '%ancestral hall%'
                OR t ~ $wb$\ystele\y$wb$
                OR t LIKE '%stone carving%'
                OR t ~ $wb$\yarchaeological\y$wb$
                OR t ~ $wb$\yrelic\y$wb$
                OR t LIKE '%cultural relic%'
                OR t LIKE '%heritage site%'
                OR t LIKE '%world heritage%'
                OR t ~ $wb$\yopera\y$wb$
                OR t ~ $wb$\ycalligraphy\y$wb$
                OR t ~ $wb$\ysilk\y$wb$
                OR t ~ $wb$\yceramics\y$wb$
                OR t ~ $wb$\ypottery\y$wb$
                OR t ~ $wb$\yfestival\y$wb$
                OR t ~ $wb$\ytraditional\y$wb$
                OR t ~ $wb$\yethnic\y$wb$
                OR t ~ $wb$\yminority\y$wb$
                OR t ~ $wb$\ytibetan\y$wb$
                OR t ~ $wb$\yuyghur\y$wb$
                OR t ~ $wb$\ymiao\y$wb$
                OR t ~ $wb$\ydong\y$wb$
                OR t ~ $wb$\ycostume\y$wb$
                OR t ~ $wb$\yfolk\y$wb$
                OR t ~ $wb$\yceremony\y$wb$
                OR t ~ $wb$\yritual\y$wb$
                OR t ~ $wb$\yheritage\y$wb$
                OR t ~ $wb$\yperformance\y$wb$
                OR t ~ $wb$\ycraft\y$wb$
                OR t ~ $wb$\yartisan\y$wb$
                OR t LIKE '%lantern festival%'
                OR t LIKE '%dragon boat%'
                OR t ~ $wb$\ymid-autumn\y$wb$
                OR t LIKE '%spring festival%'
                OR t LIKE '%chinese new year%'
                OR t LIKE '%lunar new year%'
                OR t LIKE '%paper cutting%'
                OR t LIKE '%shadow puppet%'
                OR t ~ $wb$\yembroidery\y$wb$
                OR t ~ $wb$\ybatik\y$wb$
                OR t ~ $wb$\ytie-dye\y$wb$
                OR t ~ $wb$\yincense\y$wb$
                OR t LIKE '%tea ceremony%'
                OR t LIKE '%tea culture%'
                OR t ~ $wb$\yhanfu\y$wb$
                OR t ~ $wb$\yqipao\y$wb$
                OR t LIKE '%lion dance%'
                OR t LIKE '%dragon dance%'
                OR t ~ $wb$\yfirecracker\y$wb$)
                THEN 'heritage_culture'::text END,
            CASE WHEN (t ~ $wb$\ymuseum\y$wb$
                OR t ~ $wb$\ygallery\y$wb$
                OR t ~ $wb$\yexhibit\y$wb$
                OR t ~ $wb$\yexhibition\y$wb$
                OR t ~ $wb$\yartifact\y$wb$
                OR t ~ $wb$\ycollection\y$wb$
                OR t LIKE '%science museum%'
                OR t LIKE '%history museum%'
                OR t LIKE '%art museum%'
                OR t ~ $wb$\yantiquity\y$wb$
                OR t LIKE '%national museum%'
                OR t LIKE '%war museum%'
                OR t ~ $wb$\ymemorial\y$wb$
                OR t LIKE '%memorial hall%'
                OR t LIKE '%art gallery%'
                OR t LIKE '%contemporary art%'
                OR t LIKE '%installation art%'
                OR t ~ $wb$\ysculpture\y$wb$
                OR t ~ $wb$\ycurator\y$wb$
                OR t ~ $wb$\yskyline\y$wb$
                OR t ~ $wb$\yskyscraper\y$wb$
                OR t ~ $wb$\ymodern\y$wb$
                OR t ~ $wb$\yfuturistic\y$wb$
                OR t ~ $wb$\yarchitecture\y$wb$
# Sourced from Calplus (https://github.com/Calplus)
                OR t ~ $wb$\ytower\y$wb$
                OR t ~ $wb$\ybuilding\y$wb$
                OR t LIKE '%light show%'
                OR t ~ $wb$\yneon\y$wb$
                OR t ~ $wb$\ycyberpunk\y$wb$
                OR t ~ $wb$\yurban\y$wb$
                OR t ~ $wb$\ydesign\y$wb$
                OR t ~ $wb$\ylandmark\y$wb$
                OR t LIKE '%art district%'
                OR t LIKE '%street art%'
                OR t ~ $wb$\ygraffiti\y$wb$
                OR t ~ $wb$\ymural\y$wb$
                OR t ~ $wb$\ycreative\y$wb$
                OR t ~ $wb$\yinstallation\y$wb$
                OR t ~ $wb$\ybund\y$wb$
                OR t ~ $wb$\ypudong\y$wb$
                OR t ~ $wb$\ycbd\y$wb$
                OR t ~ $wb$\ycolonial\y$wb$
                OR t LIKE '%art deco%'
                OR t ~ $wb$\ybrutalist\y$wb$
                OR t ~ $wb$\yglass\y$wb$
                OR t ~ $wb$\ysteel\y$wb$
                OR t LIKE '%observation deck%'
                OR t ~ $wb$\ybridge\y$wb$
                OR t ~ $wb$\ydam\y$wb$
                OR t ~ $wb$\yconcrete\y$wb$
                OR t ~ $wb$\yfacade\y$wb$)
                THEN 'museums_art'::text END,
            CASE WHEN (t LIKE '%street food%'
                OR t LIKE '%night market%'
                OR t ~ $wb$\ysnack\y$wb$
                OR t ~ $wb$\yhawker\y$wb$
                OR t LIKE '%food stall%'
                OR t LIKE '%cheap eats%'
                OR t LIKE '%food street%'
                OR t ~ $wb$\ybbq\y$wb$
                OR t ~ $wb$\ygrill\y$wb$
                OR t ~ $wb$\yskewer\y$wb$
                OR t ~ $wb$\ywonton\y$wb$
                OR t ~ $wb$\yjianbing\y$wb$
                OR t ~ $wb$\ybaozi\y$wb$
                OR t LIKE '%snack street%'
                OR t LIKE '%da pai dang%'
                OR t LIKE '%local food%'
                OR t LIKE '%lamb skewer%'
                OR t ~ $wb$\ychuanr\y$wb$
                OR t LIKE '%stinky tofu%'
                OR t ~ $wb$\ytanghulu\y$wb$
                OR t ~ $wb$\yroujiamo\y$wb$
                OR t ~ $wb$\yxiaolongbao\y$wb$
                OR t ~ $wb$\yfried\y$wb$
                OR t ~ $wb$\ypancake\y$wb$
                OR t ~ $wb$\ybingfen\y$wb$
                OR t ~ $wb$\ymalatang\y$wb$
                OR t LIKE '%food market%'
                OR t LIKE '%wet market%'
                OR t LIKE '%morning market%'
                OR t ~ $wb$\yrestaurant\y$wb$
                OR t ~ $wb$\ycuisine\y$wb$
                OR t ~ $wb$\ydish\y$wb$
                OR t ~ $wb$\ymeal\y$wb$
                OR t ~ $wb$\ydelicious\y$wb$
                OR t ~ $wb$\ytaste\y$wb$
                OR t ~ $wb$\ynoodle\y$wb$
                OR t ~ $wb$\ydumpling\y$wb$
                OR t ~ $wb$\yhotpot\y$wb$
                OR t ~ $wb$\ysichuan\y$wb$
                OR t ~ $wb$\ycantonese\y$wb$
                OR t LIKE '%dim sum%'
                OR t ~ $wb$\yspicy\y$wb$
                OR t ~ $wb$\yauthentic\y$wb$
                OR t LIKE '%local cuisine%'
                OR t LIKE '%fine dining%'
                OR t ~ $wb$\ymichelin\y$wb$
                OR t ~ $wb$\ygourmet\y$wb$
                OR t LIKE '%tea house%'
                OR t ~ $wb$\ytea\y$wb$
                OR t ~ $wb$\ypu-erh\y$wb$
                OR t LIKE '%peking duck%'
                OR t LIKE '%mapo tofu%'
                OR t LIKE '%kung pao%'
                OR t ~ $wb$\ycongee\y$wb$
                OR t LIKE '%fried rice%'
                OR t LIKE '%spring roll%'
                OR t ~ $wb$\ymooncake\y$wb$
                OR t ~ $wb$\ysteamed\y$wb$
                OR t ~ $wb$\ybraised\y$wb$
                OR t ~ $wb$\yroasted\y$wb$
                OR t LIKE '%hot pot%'
                OR t ~ $wb$\yseafood\y$wb$
                OR t ~ $wb$\yvegetarian\y$wb$
                OR t ~ $wb$\yvegan\y$wb$
                OR t ~ $wb$\yhalal\y$wb$
                OR t LIKE '%food tour%'
                OR t LIKE '%cooking class%'
                OR t ~ $wb$\yrecipe\y$wb$
                OR t ~ $wb$\ychef\y$wb$
                OR t ~ $wb$\yflavor\y$wb$)
                THEN 'food_dining'::text END,
            CASE WHEN (t ~ $wb$\ylandscape\y$wb$
                OR t ~ $wb$\ykarst\y$wb$
                OR t ~ $wb$\ylimestone\y$wb$
                OR t ~ $wb$\ycave\y$wb$
                OR t LIKE '%river cruise%'
                OR t ~ $wb$\yscenic\y$wb$
                OR t ~ $wb$\ypanorama\y$wb$
                OR t ~ $wb$\yviewpoint\y$wb$
                OR t ~ $wb$\ywaterfall\y$wb$
                OR t ~ $wb$\ylake\y$wb$
                OR t ~ $wb$\yvista\y$wb$
                OR t LIKE '%national park%'
                OR t ~ $wb$\ygeopark\y$wb$
                OR t LIKE '%natural wonder%'
# Source: github.com/Calplus
                OR t ~ $wb$\ydesert\y$wb$
                OR t ~ $wb$\ygrassland\y$wb$
                OR t ~ $wb$\ysteppe\y$wb$
                OR t ~ $wb$\ydune\y$wb$
                OR t ~ $wb$\ygobi\y$wb$
                OR t LIKE '%silk road%'
                OR t LIKE '%terraced fields%'
                OR t LIKE '%rice terrace%'
                OR t LIKE '%bamboo forest%'
                OR t ~ $wb$\yrainforest\y$wb$
                OR t ~ $wb$\yplateau\y$wb$
                OR t ~ $wb$\yprairie\y$wb$
                OR t ~ $wb$\ywetland\y$wb$
                OR t ~ $wb$\yglacier\y$wb$
                OR t LIKE '%hot spring%'
                OR t ~ $wb$\ysunrise\y$wb$
                OR t ~ $wb$\ysunset\y$wb$
                OR t LIKE '%golden hour%'
                OR t ~ $wb$\ymist\y$wb$
                OR t ~ $wb$\yfog\y$wb$
                OR t ~ $wb$\yreflection\y$wb$
                OR t ~ $wb$\yjiuzhaigou\y$wb$
                OR t ~ $wb$\yzhangjiajie\y$wb$
                OR t ~ $wb$\yguilin\y$wb$
                OR t ~ $wb$\yyangshuo\y$wb$
                OR t ~ $wb$\ydanxia\y$wb$
                OR t ~ $wb$\yphoto\y$wb$
                OR t ~ $wb$\yphotography\y$wb$
                OR t ~ $wb$\yinstagrammable\y$wb$
                OR t ~ $wb$\yphotogenic\y$wb$
                OR t ~ $wb$\ycamera\y$wb$
                OR t ~ $wb$\ypicture\y$wb$
                OR t ~ $wb$\yshot\y$wb$
                OR t ~ $wb$\yselfie\y$wb$
                OR t LIKE '%scenic spot%'
                OR t ~ $wb$\yinsta-worthy\y$wb$
                OR t ~ $wb$\yxiaohongshu\y$wb$
                OR t ~ $wb$\ydrone\y$wb$
                OR t ~ $wb$\ytimelapse\y$wb$
                OR t ~ $wb$\ypanoramic\y$wb$
                OR t ~ $wb$\yportrait\y$wb$
                OR t LIKE '%landscape photo%'
                OR t ~ $wb$\ylens\y$wb$
                OR t ~ $wb$\ytripod\y$wb$
                OR t ~ $wb$\yfilter\y$wb$
                OR t ~ $wb$\yedit\y$wb$
                OR t ~ $wb$\ylightroom\y$wb$
                OR t ~ $wb$\ycapture\y$wb$)
                THEN 'nature_scenery'::text END,
            CASE WHEN (t ~ $wb$\ybeach\y$wb$
                OR t ~ $wb$\ycoast\y$wb$
                OR t ~ $wb$\ycoastal\y$wb$
                OR t ~ $wb$\yocean\y$wb$
                OR t ~ $wb$\ysea\y$wb$
                OR t ~ $wb$\yisland\y$wb$
                OR t ~ $wb$\ysurfing\y$wb$
                OR t ~ $wb$\ytropical\y$wb$
                OR t ~ $wb$\yresort\y$wb$
                OR t ~ $wb$\yseaside\y$wb$
                OR t ~ $wb$\ybay\y$wb$
                OR t ~ $wb$\ylagoon\y$wb$
                OR t ~ $wb$\ysnorkeling\y$wb$
                OR t ~ $wb$\ydiving\y$wb$
                OR t ~ $wb$\ymarine\y$wb$
                OR t ~ $wb$\ycoral\y$wb$
                OR t ~ $wb$\ysand\y$wb$
                OR t ~ $wb$\ywave\y$wb$
                OR t ~ $wb$\ytide\y$wb$
                OR t ~ $wb$\yboardwalk\y$wb$
                OR t ~ $wb$\ysanya\y$wb$
                OR t ~ $wb$\yhainan\y$wb$
                OR t ~ $wb$\ybeihai\y$wb$
                OR t ~ $wb$\yweihai\y$wb$
                OR t LIKE '%qingdao beach%'
                OR t LIKE '%paradise island%'
                OR t ~ $wb$\ysunbathing\y$wb$)
                THEN 'beaches_coastal'::text END,
            CASE WHEN (t ~ $wb$\yhike\y$wb$
                OR t ~ $wb$\yhiking\y$wb$
                OR t ~ $wb$\ytrail\y$wb$
                OR t ~ $wb$\ytrek\y$wb$
                OR t ~ $wb$\ytrekking\y$wb$
                OR t ~ $wb$\ymountain\y$wb$
                OR t ~ $wb$\yclimb\y$wb$
                OR t ~ $wb$\ysummit\y$wb$
                OR t ~ $wb$\ypeak\y$wb$
                OR t ~ $wb$\yelevation\y$wb$
                OR t ~ $wb$\ybasecamp\y$wb$
                OR t ~ $wb$\yridge\y$wb$
                OR t ~ $wb$\yvalley\y$wb$
                OR t ~ $wb$\ygorge\y$wb$
                OR t ~ $wb$\ycanyon\y$wb$
                OR t LIKE '%scenic walk%'
                OR t ~ $wb$\ymountaineering\y$wb$
                OR t ~ $wb$\ybackpacking\y$wb$
                OR t ~ $wb$\yaltitude\y$wb$
                OR t ~ $wb$\ycamping\y$wb$
                OR t ~ $wb$\yoverlook\y$wb$
                OR t ~ $wb$\ypass\y$wb$
                OR t ~ $wb$\yascent\y$wb$
                OR t ~ $wb$\ydescent\y$wb$
                OR t ~ $wb$\yswitchback\y$wb$
                OR t ~ $wb$\yhuangshan\y$wb$
                OR t ~ $wb$\ytaishan\y$wb$
                OR t ~ $wb$\yemeishan\y$wb$
                OR t ~ $wb$\yhuashan\y$wb$
                OR t ~ $wb$\ywutaishan\y$wb$
                OR t ~ $wb$\yski\y$wb$
                OR t ~ $wb$\yskiing\y$wb$
                OR t ~ $wb$\ysnowboard\y$wb$
                OR t ~ $wb$\yice\y$wb$
                OR t ~ $wb$\ysnow\y$wb$
                OR t ~ $wb$\ywinter\y$wb$
# calplus source
                OR t LIKE '%ice festival%'
                OR t ~ $wb$\ysledding\y$wb$
                OR t ~ $wb$\yfrozen\y$wb$
                OR t LIKE '%winter sports%'
                OR t LIKE '%harbin ice%'
                OR t LIKE '%ice sculpture%'
                OR t LIKE '%ice world%'
                OR t LIKE '%snow festival%'
                OR t LIKE '%ice skating%'
                OR t ~ $wb$\ycurling\y$wb$
                OR t LIKE '%ice hockey%'
                OR t ~ $wb$\ysnowfall\y$wb$
                OR t ~ $wb$\yfrost\y$wb$
                OR t ~ $wb$\ysub-zero\y$wb$)
                THEN 'hiking_adventure'::text END,
            CASE WHEN (t ~ $wb$\ypanda\y$wb$
                OR t ~ $wb$\ywildlife\y$wb$
                OR t ~ $wb$\yanimal\y$wb$
                OR t ~ $wb$\ybird\y$wb$
                OR t ~ $wb$\ybirdwatching\y$wb$
                OR t ~ $wb$\yconservation\y$wb$
                OR t ~ $wb$\yzoo\y$wb$
                OR t ~ $wb$\ysanctuary\y$wb$
                OR t LIKE '%nature reserve%'
                OR t ~ $wb$\ymonkey\y$wb$
                OR t ~ $wb$\yendangered\y$wb$
                OR t ~ $wb$\ybotanical\y$wb$
                OR t ~ $wb$\ygarden\y$wb$
                OR t ~ $wb$\yflora\y$wb$
                OR t ~ $wb$\yfauna\y$wb$
                OR t ~ $wb$\ysafari\y$wb$
                OR t LIKE '%national park%'
                OR t LIKE '%red panda%'
                OR t LIKE '%golden monkey%'
                OR t LIKE '%snow leopard%'
                OR t ~ $wb$\ycrane\y$wb$
                OR t ~ $wb$\ydolphin\y$wb$
                OR t ~ $wb$\ybutterfly\y$wb$
                OR t ~ $wb$\yaquarium\y$wb$
                OR t LIKE '%breeding center%'
                OR t LIKE '%research base%')
                THEN 'wildlife'::text END,
            CASE WHEN (t ~ $wb$\ynightlife\y$wb$
                OR t ~ $wb$\ybar\y$wb$
                OR t ~ $wb$\yclub\y$wb$
                OR t ~ $wb$\yclubbing\y$wb$
                OR t ~ $wb$\ypub\y$wb$
                OR t ~ $wb$\ylounge\y$wb$
                OR t ~ $wb$\yrooftop\y$wb$
                OR t LIKE '%live music%'
                OR t ~ $wb$\yconcert\y$wb$
                OR t ~ $wb$\ydj\y$wb$
                OR t ~ $wb$\yparty\y$wb$
                OR t ~ $wb$\yentertainment\y$wb$
                OR t ~ $wb$\ykaraoke\y$wb$
                OR t LIKE '%craft beer%'
                OR t ~ $wb$\ycocktail\y$wb$
                OR t ~ $wb$\ynightclub\y$wb$
                OR t ~ $wb$\ydisco\y$wb$
                OR t LIKE '%happy hour%'
                OR t ~ $wb$\yspeakeasy\y$wb$
                OR t LIKE '%wine bar%'
                OR t ~ $wb$\yjazz\y$wb$
                OR t ~ $wb$\ynightspot\y$wb$
                OR t LIKE '%after dark%'
                OR t LIKE '%neon lights%'
                OR t LIKE '%night scene%'
                OR t LIKE '%night view%'
                OR t ~ $wb$\yshopping\y$wb$
                OR t ~ $wb$\ymall\y$wb$
                OR t ~ $wb$\ymarket\y$wb$
                OR t ~ $wb$\ysouvenir\y$wb$
                OR t ~ $wb$\yboutique\y$wb$
                OR t ~ $wb$\ybrand\y$wb$
                OR t ~ $wb$\yfashion\y$wb$
                OR t ~ $wb$\yluxury\y$wb$
                OR t ~ $wb$\youtlet\y$wb$
                OR t ~ $wb$\ywholesale\y$wb$
                OR t ~ $wb$\ytech\y$wb$
                OR t ~ $wb$\yelectronics\y$wb$
                OR t ~ $wb$\yantique\y$wb$
                OR t ~ $wb$\ybazaar\y$wb$
                OR t ~ $wb$\yduty-free\y$wb$
                OR t ~ $wb$\ybargain\y$wb$
                OR t LIKE '%silk market%'
                OR t LIKE '%pearl market%'
                OR t ~ $wb$\yjade\y$wb$
                OR t LIKE '%tea shop%'
                OR t LIKE '%flea market%'
                OR t ~ $wb$\yvintage\y$wb$
                OR t LIKE '%department store%'
                OR t ~ $wb$\yhaul\y$wb$
                OR t ~ $wb$\ybuy\y$wb$
                OR t ~ $wb$\ypurchase\y$wb$)
                THEN 'nightlife_entertainment'::text END,
            CASE WHEN (t ~ $wb$\yspa\y$wb$
                OR t ~ $wb$\ywellness\y$wb$
                OR t LIKE '%traditional chinese medicine%'
                OR t ~ $wb$\ytcm\y$wb$
                OR t ~ $wb$\yacupuncture\y$wb$
                OR t ~ $wb$\ymassage\y$wb$
                OR t LIKE '%tai chi%'
                OR t ~ $wb$\yqigong\y$wb$
                OR t ~ $wb$\ymeditation\y$wb$
                OR t ~ $wb$\yretreat\y$wb$
                OR t ~ $wb$\yrelaxation\y$wb$
                OR t ~ $wb$\yhealth\y$wb$
                OR t ~ $wb$\ythermal\y$wb$
                OR t LIKE '%martial arts%'
                OR t LIKE '%kung fu%'
                OR t ~ $wb$\yshaolin\y$wb$
                OR t LIKE '%wing chun%'
                OR t ~ $wb$\yyoga\y$wb$
# Sourced from Calplus (https://github.com/Calplus)
                OR t ~ $wb$\ymindfulness\y$wb$
                OR t ~ $wb$\ydetox\y$wb$
                OR t ~ $wb$\yhealing\y$wb$
                OR t ~ $wb$\yherbal\y$wb$
                OR t ~ $wb$\ycupping\y$wb$
                OR t ~ $wb$\ymoxibustion\y$wb$
                OR t ~ $wb$\yhotel\y$wb$
                OR t ~ $wb$\yhostel\y$wb$
                OR t ~ $wb$\yroom\y$wb$
                OR t ~ $wb$\ystay\y$wb$
                OR t ~ $wb$\ybed\y$wb$
                OR t ~ $wb$\yairbnb\y$wb$
                OR t ~ $wb$\yresort\y$wb$
                OR t ~ $wb$\ylodge\y$wb$
                OR t ~ $wb$\yguesthouse\y$wb$
                OR t ~ $wb$\yvilla\y$wb$
                OR t ~ $wb$\ymotel\y$wb$
                OR t ~ $wb$\yamenities\y$wb$
                OR t ~ $wb$\ylobby\y$wb$
                OR t ~ $wb$\ypool\y$wb$
                OR t ~ $wb$\ysuite\y$wb$
                OR t ~ $wb$\ybooking\y$wb$
                OR t ~ $wb$\ycheck-in\y$wb$
                OR t ~ $wb$\ycheckout\y$wb$
                OR t ~ $wb$\yreception\y$wb$
                OR t ~ $wb$\yconcierge\y$wb$
                OR t ~ $wb$\ydormitory\y$wb$
                OR t ~ $wb$\ybunk\y$wb$
                OR t LIKE '%capsule hotel%'
                OR t ~ $wb$\yhomestay\y$wb$
                OR t LIKE '%boutique hotel%'
                OR t LIKE '%five star%'
                OR t LIKE '%luxury hotel%'
                OR t LIKE '%budget hotel%')
                THEN 'wellness_relaxation'::text END,
            CASE WHEN (t ~ $wb$\yprice\y$wb$
                OR t ~ $wb$\ycost\y$wb$
                OR t ~ $wb$\yexpensive\y$wb$
                OR t ~ $wb$\ycheap\y$wb$
                OR t ~ $wb$\ybudget\y$wb$
                OR t ~ $wb$\yaffordable\y$wb$
                OR t ~ $wb$\yworth\y$wb$
                OR t ~ $wb$\ymoney\y$wb$
                OR t ~ $wb$\yfee\y$wb$
                OR t ~ $wb$\yticket\y$wb$
                OR t ~ $wb$\yfree\y$wb$
                OR t ~ $wb$\yoverpriced\y$wb$
                OR t ~ $wb$\ybargain\y$wb$
                OR t ~ $wb$\yyuan\y$wb$
                OR t ~ $wb$\yrmb\y$wb$
                OR t ~ $wb$\ydiscount\y$wb$
                OR t ~ $wb$\ydeal\y$wb$
                OR t ~ $wb$\yvalue\y$wb$
                OR t ~ $wb$\yrip-off\y$wb$
                OR t ~ $wb$\ybackpacker\y$wb$
                OR t ~ $wb$\yeconomical\y$wb$
                OR t LIKE '%save money%'
                OR t ~ $wb$\ysplurge\y$wb$
                OR t ~ $wb$\ymid-range\y$wb$
                OR t LIKE '%hostel price%'
                OR t LIKE '%entrance fee%'
                OR t ~ $wb$\yadmission\y$wb$
                OR t ~ $wb$\ysafe\y$wb$
                OR t ~ $wb$\yunsafe\y$wb$
                OR t ~ $wb$\yscam\y$wb$
                OR t ~ $wb$\ytheft\y$wb$
                OR t ~ $wb$\ycrime\y$wb$
                OR t ~ $wb$\ypolice\y$wb$
                OR t ~ $wb$\ysecurity\y$wb$
                OR t ~ $wb$\ydanger\y$wb$
                OR t ~ $wb$\yrobbery\y$wb$
                OR t ~ $wb$\ypickpocket\y$wb$
                OR t ~ $wb$\yfraud\y$wb$
                OR t ~ $wb$\ywarning\y$wb$
                OR t LIKE '%tourist trap%'
                OR t ~ $wb$\ycareful\y$wb$
                OR t ~ $wb$\ycaution\y$wb$
                OR t ~ $wb$\yrisk\y$wb$
                OR t ~ $wb$\yemergency\y$wb$
                OR t ~ $wb$\yhospital\y$wb$
                OR t ~ $wb$\yinsurance\y$wb$
                OR t ~ $wb$\ylost\y$wb$
                OR t ~ $wb$\ystolen\y$wb$
                OR t ~ $wb$\yharassment\y$wb$
                OR t LIKE '%solo travel%'
                OR t LIKE '%travel advisory%')
                THEN 'budget_safety'::text END,
            CASE WHEN (t ~ $wb$\ytrain\y$wb$
                OR t ~ $wb$\ybus\y$wb$
                OR t ~ $wb$\ytaxi\y$wb$
                OR t ~ $wb$\yflight\y$wb$
                OR t ~ $wb$\ymetro\y$wb$
                OR t ~ $wb$\ysubway\y$wb$
                OR t ~ $wb$\yuber\y$wb$
                OR t ~ $wb$\ydidi\y$wb$
                OR t ~ $wb$\ydrive\y$wb$
                OR t ~ $wb$\yairport\y$wb$
                OR t ~ $wb$\ystation\y$wb$
                OR t LIKE '%car rental%'
                OR t ~ $wb$\yferry\y$wb$
                OR t ~ $wb$\yboat\y$wb$
                OR t ~ $wb$\ybicycle\y$wb$
                OR t ~ $wb$\yhighway\y$wb$
                OR t ~ $wb$\ytransit\y$wb$
                OR t LIKE '%high-speed rail%'
                OR t LIKE '%bullet train%'
                OR t ~ $wb$\ycommute\y$wb$
                OR t ~ $wb$\ytransfer\y$wb$
                OR t ~ $wb$\yticket\y$wb$
                OR t ~ $wb$\yboarding\y$wb$
                OR t ~ $wb$\yluggage\y$wb$
                OR t ~ $wb$\ydelay\y$wb$
                OR t ~ $wb$\yschedule\y$wb$
# Source: github.com/Calplus
                OR t ~ $wb$\yroute\y$wb$
                OR t ~ $wb$\yconnection\y$wb$
                OR t LIKE '%bike share%'
                OR t ~ $wb$\ye-bike\y$wb$
                OR t ~ $wb$\yscooter\y$wb$
                OR t ~ $wb$\ywifi\y$wb$
                OR t ~ $wb$\yinternet\y$wb$
                OR t ~ $wb$\yvpn\y$wb$
                OR t ~ $wb$\ysignal\y$wb$
                OR t ~ $wb$\y4g\y$wb$
                OR t ~ $wb$\y5g\y$wb$
                OR t ~ $wb$\ywechat\y$wb$
                OR t ~ $wb$\yalipay\y$wb$
                OR t ~ $wb$\yapp\y$wb$
                OR t ~ $wb$\ydigital\y$wb$
                OR t ~ $wb$\yfirewall\y$wb$
                OR t LIKE '%great firewall%'
                OR t LIKE '%mobile payment%'
                OR t LIKE '%sim card%'
                OR t ~ $wb$\ydata\y$wb$
                OR t ~ $wb$\yroaming\y$wb$
                OR t ~ $wb$\yesim\y$wb$
                OR t ~ $wb$\yhotspot\y$wb$
                OR t LIKE '%qr code%'
                OR t ~ $wb$\yonline\y$wb$
                OR t ~ $wb$\ydownload\y$wb$
                OR t ~ $wb$\ystreaming\y$wb$
                OR t ~ $wb$\ycensorship\y$wb$
                OR t ~ $wb$\yenglish\y$wb$
                OR t ~ $wb$\ylanguage\y$wb$
                OR t ~ $wb$\ycommunication\y$wb$
                OR t ~ $wb$\ytranslate\y$wb$
                OR t ~ $wb$\ymandarin\y$wb$
                OR t ~ $wb$\yunderstand\y$wb$
                OR t ~ $wb$\ysign\y$wb$
                OR t ~ $wb$\yforeign\y$wb$
                OR t ~ $wb$\yforeigner\y$wb$
                OR t ~ $wb$\yexpat\y$wb$
                OR t LIKE '%culture shock%'
                OR t ~ $wb$\ybarrier\y$wb$
                OR t ~ $wb$\ytourist-friendly\y$wb$
                OR t ~ $wb$\ybilingual\y$wb$
                OR t ~ $wb$\ysignage\y$wb$
                OR t ~ $wb$\yspeak\y$wb$
                OR t LIKE '%google translate%'
                OR t LIKE '%language barrier%'
                OR t ~ $wb$\ygesture\y$wb$
                OR t ~ $wb$\yphrasebook\y$wb$
                OR t LIKE '%local language%'
                OR t ~ $wb$\ydialect\y$wb$
                OR t ~ $wb$\yputonghua\y$wb$)
                THEN 'transport_connectivity'::text END,
            CASE WHEN (t ~ $wb$\yweather\y$wb$
                OR t LIKE '%air quality%'
                OR t ~ $wb$\ypollution\y$wb$
                OR t ~ $wb$\ysmog\y$wb$
                OR t ~ $wb$\yaqi\y$wb$
                OR t ~ $wb$\yhot\y$wb$
                OR t ~ $wb$\ycold\y$wb$
                OR t ~ $wb$\yrain\y$wb$
                OR t ~ $wb$\yhumid\y$wb$
                OR t ~ $wb$\ysunny\y$wb$
                OR t ~ $wb$\ycloudy\y$wb$
                OR t ~ $wb$\ysnow\y$wb$
                OR t ~ $wb$\ytemperature\y$wb$
                OR t ~ $wb$\yseason\y$wb$
                OR t ~ $wb$\yhaze\y$wb$
                OR t ~ $wb$\ydust\y$wb$
                OR t ~ $wb$\ypm2\.5\y$wb$
                OR t LIKE '%clear sky%'
                OR t ~ $wb$\yfog\y$wb$
                OR t ~ $wb$\yfrost\y$wb$
                OR t ~ $wb$\ymonsoon\y$wb$
                OR t ~ $wb$\ytyphoon\y$wb$
                OR t ~ $wb$\yheatwave\y$wb$
                OR t ~ $wb$\yhumidity\y$wb$
                OR t ~ $wb$\yclimate\y$wb$
                OR t ~ $wb$\yforecast\y$wb$
                OR t LIKE '%best time to visit%'
                OR t LIKE '%rainy season%'
                OR t LIKE '%dry season%')
                THEN 'weather_planning'::text END,
            CASE WHEN (t ~ $wb$\yfamily\y$wb$
                OR t ~ $wb$\ykids\y$wb$
                OR t ~ $wb$\ychildren\y$wb$
                OR t LIKE '%theme park%'
                OR t ~ $wb$\yplayground\y$wb$
                OR t ~ $wb$\yfamily-friendly\y$wb$
                OR t ~ $wb$\ydisney\y$wb$
                OR t ~ $wb$\ywaterpark\y$wb$
                OR t ~ $wb$\yzoo\y$wb$
                OR t ~ $wb$\yaquarium\y$wb$
                OR t ~ $wb$\yamusement\y$wb$
                OR t ~ $wb$\ychild-friendly\y$wb$
                OR t ~ $wb$\ystroller\y$wb$
                OR t ~ $wb$\ybaby\y$wb$
                OR t ~ $wb$\ytoddler\y$wb$
                OR t LIKE '%family trip%'
                OR t LIKE '%family vacation%'
                OR t ~ $wb$\ydisneyland\y$wb$
                OR t LIKE '%ocean park%'
                OR t LIKE '%happy valley%'
                OR t ~ $wb$\ychimelong\y$wb$
                OR t ~ $wb$\ylegoland\y$wb$)
                THEN 'family_kids'::text END
        ], NULL) AS cats
    FROM (
        SELECT id,
            lower(COALESCE(text,'')) AS t
        FROM instagram_crawl.ig_comments
        WHERE categories IS NULL
    ) src
) computed
WHERE tbl.id = computed.id;
