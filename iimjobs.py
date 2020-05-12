from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
import time
import csv


TIMEOUT = 60
COMPANIES_URL = 'https://www.iimjobs.com/c/finance-jobs-13.html'
FILE_NAME = 'jobs_info.csv'
SCROLL_PAUSE_TIME = 3
#FILE_NAME = 'jobs.csv'
#jobs_info = []


def get_working_driver(url, element_to_load):
    try:
        driver = webdriver.Chrome(
                        #executable_path='/Users/rishitmac/Documents/JobScraper/indeed_scrapper/chromedriver')
                        executable_path='/Users/aceinna_rishit/Documents/ScrapperScript/iimjobs/chromedriver')
        driver.set_page_load_timeout(TIMEOUT)
        #driver.maximize_window()
    except Exception as e:
        print('Something went wrong...')
        print(e)
        time.sleep(TIMEOUT)
        return get_working_driver(url, element_to_load)

    success = False
    try:
        driver.get(url)
        success = True
    except TimeoutException as ex:
        print('Timed out waiting for page to load... ')
        print(str(ex))
        driver.navigate().refresh()
    #print("Moving on\r\n")
    if success and page_loaded(driver, element_to_load):
        return driver
    else:
        time.sleep(30)
        driver.quit()
        return get_working_driver(url, element_to_load)


def page_loaded(driver, element_to_load):
    if 'unusual activity coming from your computer network' in driver.page_source:
        print('Bot detected and captcha')
        return 0
    if 'temporarily blocked for security reasons' in driver.page_source:
        print('Bot detected and blocked')
        return 0
    if "'<div class='icon icon-generic'" in driver.page_source:
        print('Bad connection')
        return 0
    try:
        #print("Waiting for TBODY content")
        WebDriverWait(driver, TIMEOUT).until(ec.presence_of_element_located((By.ID, element_to_load)))
        print("Driver Ready")
        return 1
    except TimeoutException:
        print('Timed out waiting for page to load (Page_loader)... ')
        return 0


def write_to_csv(info_dicts, fieldnames):
	with open(FILE_NAME, 'a+', newline='') as out_file:
		writer = csv.DictWriter(out_file, fieldnames=fieldnames)
        #writer.writeheader()
		for info_dict in info_dicts:
			try:
				writer.writerow(info_dict)
			except UnicodeEncodeError:
				print(info_dict)
				pass
	print('Wrote {0} rows to {1}'.format(len(info_dicts), FILE_NAME))

def write_to_csv_by_line(info_dict, fieldnames):
	with open(FILE_NAME, 'a+', newline='') as out_file:
		writer = csv.DictWriter(out_file, fieldnames=fieldnames, delimiter='\t')
		try:
			writer.writerow(info_dict)
		except UnicodeEncodeError:
			print(info_dict)
			pass

def is_scrapped(sub_category):
    with open(FILE_NAME, 'r') as database_file:
        reader = csv.DictReader(database_file)
        for line in reader:
            if str(sub_category) in line['sub_category_name']:
                return True
    return False

def extract_job_info(driver, link):
    salary = -1
    experience = -1
    '''  Open Job in a new Tab '''
    # Save the window opener (current window, do not mistaken with tab... not the same)
    main_window = driver.current_window_handle

    # Open the link in a new tab by sending key strokes on the element
    # Use: Keys.CONTROL + Keys.SHIFT + Keys.RETURN to open tab on top of the stack
    link.send_keys(Keys.CONTROL + Keys.RETURN)

    # Switch to last opened tab
    driver.switch_to.window(driver.window_handles[-1])

    # Save Job page handle
    job_page = driver.current_window_handle
    time.sleep(0.7)

    ''' Process job'''

    job_description = driver.find_element_by_class_name('jobsearch-jobDescriptionText')

    # Read Sub Headings/ Header with symbols
    meta_data = driver.find_elements_by_xpath("//*[@class='jobsearch-JobMetadataHeader-itemWithIcon icl-u-textColor--secondary icl-u-xs-mt--xs']")
    for data in meta_data:
        # Get salary
        #Look for INR symbol in string
        if u'\u20B9' in data.text:
            salary = data.text
        # get experience
        elif "experience" in data.text:
            experience = data.text
        # get other information
        else:
            other = data.text

    description = { 'salary' : salary,
                    'experience' : experience,
                    'other_info': other,
                    'jd': job_description.text}

    ''' Close Job tab & switch to main window '''
    # Close Job_page
    driver.close();

    # Switch to main page
    driver.switch_to.window(main_window);
    return description


def extract_job_Data(driver, job_block, category, sub_category):
    print("Extracting information for ", job_block.find_element_by_class_name('title').text)
    link = job_block.find_element_by_css_selector('h2.title > a')
    jd = extract_job_info(driver, link)
    #print("salary ", jd['salary'],jd['experience'],jd['jd'] )
    job_info = {'category_name': category,
                'sub_category_name': sub_category,
                'title': job_block.find_element_by_class_name('title').text,
                'URL': job_block.find_element_by_css_selector('h2.title > a').get_attribute('href'),
                'company': job_block.find_element_by_class_name('company').text,
                'salary': jd['salary'],
                'experience': jd['experience'],
                'other_info': jd['other_info'],
                'description': jd['jd']
                }

    return job_info


def get_jobs_info(driver, sub_category, jobs):
    next_page_available = True
    company_info = {}
    count = 0
    total = ""
    page_count = 1

    # Save the window opener (current window, do not mistaken with tab... not the same)
    main_window = driver.current_window_handle
    # open a new tab
    driver.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 't')
    # open link in above created new tab
    driver.get(sub_category['link'])
    # Make last opened tab active
    driver.switch_to.window(driver.window_handles[-1])
    # Save Job page handle
    job_page = driver.current_window_handle
    time.sleep(0.4)

    try:

        while next_page_available:
            next_page_available = True

            resultCol = driver.find_elements_by_xpath("//table[2]/tbody/tr/td/table[1]/tbody/tr/td[1]")
            if resultCol:
                # find job blocks
                for item in resultCol:

                    job_blocks = item.find_elements_by_xpath("//div[@class='jobsearch-SerpJobCard unifiedRow row result clickcard']")

                    if job_blocks:
                        for block in job_blocks:
                            #print(block.text)
                            job = extract_job_Data(driver, block, sub_category['category_name'],sub_category['sub_category_name'] )
                            if job:
                                #write_to_csv('companies_info.csv', job, ['category_name','sub_category_name','title', 'URL', 'company', 'salary', 'experience', 'other_info', 'description'])
                                jobs.append(job)

                            print("=======================", page_count)

                # find next page link
                pagination = driver.find_element_by_class_name('pagination')
                if not pagination:
                    print("pagination-list not found")

                # get link for next page number
                try:
                    next_page_link = pagination.find_element_by_link_text(str(page_count+1)).get_attribute('href')
                    #print("Next Page Link", next_page_link)
                except NoSuchElementException as ex:
                    # no next page available when page_number + 1 is not found
                    next_page_available = False

                # loop through all the pages
                page_count = page_count + 1

                # Go to next page if available
                if next_page_available:
                    driver.get(next_page_link)
                    time.sleep(0.4)

            else:
                print("No result colum")

    except NoSuchElementException as ex:
        print("Can't find class name " + str(ex))
    return jobs

def get_sub_categories_from_web(driver, category, sub_categories_info):
    # Save the window opener (current window, do not mistaken with tab... not the same)
    main_window = driver.current_window_handle
    # open a new tab
    driver.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 't')
    # open link in above created new tab
    driver.get(category['link'])
    # Make last opened tab active
    driver.switch_to.window(driver.window_handles[-1])
    # Save Job page handle
    sub_category_page = driver.current_window_handle
    time.sleep(0.4)
    # find sub categories
    sub_category_titles = driver.find_element_by_id('titles')
    #print(sub_category_titles.text)

    sub_categories = sub_category_titles.find_elements_by_class_name('job')
    for sub_category in sub_categories:
        sub_category_info = {'category_name' : category['category_name'],
                            'sub_category_name': sub_category.text,
                            'link': sub_category.find_element_by_link_text(sub_category.text).get_attribute('href')}
        if sub_category_info:
            sub_categories_info.append(sub_category_info)

def get_categories_from_web(driver, categories_info):

    try:
        home = driver.find_element_by_class_name('home')
        if not home:
            print("Couldnt find Class name home")

        # Find table named "categories"
        job_categories = driver.find_element_by_id('categories')
        if not job_categories:
            print("Couldnt find job categories ")

        # Find all the categories in the Categories table
        table_data = job_categories.find_elements_by_tag_name('td')
        for data in table_data:
            category_info = {'category_name' : data.text,
                            'link': job_categories.find_element_by_link_text(data.text).get_attribute('href')}
            if category_info:
                categories_info.append(category_info)

    except NoSuchElementException as ex:
        print("Exception: " + str(ex))


def see_whats_already_scrapped(list):
    try:
        with open(FILE_NAME, 'r') as database_file:
            reader = csv.DictReader(database_file)
            for line in reader:
                sub_cat = line['sub_category_name']
                cat = line['category_name']
                if (cat,sub_cat) not in list:
                    list.append((cat,sub_cat))
    except NoSuchElementException as ex:
        print("No file/data available")
        return

def get_jobs_description(driver, link):
    # open link in above created new tab
    driver.get(link)
    block = driver.find_element_by_id('page-content-wrapper')
    jobrole = block.find_element_by_xpath("//div[@class='page-content inset ']/div[@class='info col-md-9 col-sm-9 col-xs-12 pdlr0 mnht520  ']/div[@class='details job-description ']")
    '''
    if (len(jobrole.text) < 5):
        try:
            jobrole = block.find_element_by_xpath("//div[@class='page-content inset ']/div[@class='info col-md-9 col-sm-9 col-xs-12 pdlr0 mnht520  ']/div[@class='details job-description ']/p[2]")
        except NoSuchElementException as ex:
            print("Handle")
    '''
    #print("JOB ROLE:", jobrole.text)
    WebDriverWait(driver, TIMEOUT).until(ec.presence_of_element_located((By.ID, 'jobrecinfo')))
    jobrecinfo = driver.find_element_by_id('jobrecinfo')
    description = { 'description': jobrole.text,
                    'location': (jobrecinfo.find_element_by_xpath("//span[@class='jobloc mt5 pull-left']")).text.split("\n")[1],
                    'category': (jobrecinfo.find_element_by_xpath("//span[@class='mt5 pull-left'][2]")).text.split("\n")[1],
                    'jobid': (jobrecinfo.find_element_by_xpath("//span[@class='mt5 pull-left'][3]")).text.split("\n")[1],
                    'postedon': (jobrecinfo.find_element_by_xpath("//span[@class='mt5 pull-left'][4]")).text.split("\n")[1],
                    'views': (jobrecinfo.find_element_by_xpath("//span[@class='mt5 pull-left'][5]")).text.split("\n")[1],
                    'applicants': (jobrecinfo.find_element_by_xpath("//span[@class='mt5 pull-left'][6]")).text.split("\n")[1]}
    return description

def load_job_listing(driver):

    # First While is to let webpage scroll and load jobs automatically
    last_height = driver.execute_script("return document.body.scrollHeight")            # Get scroll height
    print("last height ",last_height)
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")        # Scroll down to bottom
        time.sleep(SCROLL_PAUSE_TIME)                                                   # Wait to load page
        new_height = driver.execute_script("return document.body.scrollHeight")         # Calculate new scroll height and compare with last scroll height
        print("new_height", new_height)
        if new_height == last_height:
            print("breaking 1st")
            break
        last_height = new_height

    # Second while is to scroll and press the "Load More" button untill the end of webpage
    while True:
        try:
            WebDriverWait(driver, TIMEOUT).until(ec.presence_of_element_located((By.ID, 'navigationTrigger')))
            navtrig = driver.find_element_by_id('navigationTrigger')
            loadmorebutton = navtrig.find_element_by_xpath("//div[@class='ias_trigger']/a")
            time.sleep(2)
            loadmorebutton.click()
            time.sleep(2)
            print("Click")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print("Scroll")
            # Wait to load page
            #time.sleep(2)
            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
        except Exception as e:
            #print(e)
            break

def get_job_list(driver):
    jobs_info = []
    listing = driver.find_element_by_class_name('listing')
    if not listing:
        return null

    load_job_listing(driver)

    #get job list
    jobs = listing.find_elements_by_xpath("//span[@class='pull-left']/a[@class='mrmob5 hidden-xs']")
    for job in jobs:
        #print(job.get_attribute('text'))
        info = {'Title': job.get_attribute('text'),
                'JobLink': job.get_attribute('href')}
        jobs_info.append(info)
    return jobs_info

def get_job_details(driver, job_list):
    job_details = []
    for job in job_list:
        link = job['JobLink']
        job_title = job['Title']
        description = get_jobs_description(driver, job['JobLink'])
        if not description:
            print("Empty Description")
        print("JOB # ", job_list.index(job),"/" ,len(job_list))
        print(job_title, description['location'])
        job_detail = {'category':description['category'],
                        'link': link,
                        'title': job_title,
                        'id': description['jobid'],
                        'postedOn': description['postedon'],
                        'views': description['views'],
                        'applicants': description['applicants'],
                        'description': description['description']}

        write_to_csv_by_line(job_detail, ['category','link', 'title', 'id', 'postedOn', 'views', 'applicants', 'description'])
        job_details.append(job_detail)
    return job_details

if __name__ == '__main__':

    scrapped_pairs = []                         # list of pairs of (Category, Sub Category)
    jobs = []                                   #jobs
    all_categories = []                         # stores category <name> and <link> from the first page
    remaining_sub_categories = []               # stores sub_category <name> and <link> from the first page
    remaining_categories = []                   # Filter categories seen in file

    web_driver = get_working_driver(COMPANIES_URL, 'page-content-wrapper')

    job_list = get_job_list(web_driver)

    job_description = get_job_details(web_driver, job_list)

    '''
    get_categories_from_web(web_driver, all_categories)

    print("Total Categories : ", len(all_categories))

    # Only un-seen categories move forward
    for category in all_categories:
        all_sub_categories= []

        #get sub_categories
        get_sub_categories_from_web(web_driver, category, all_sub_categories)

        for sub_category in all_sub_categories:

            jobs_info = []                      #local job_info
            if (sub_category['category_name'], sub_category['sub_category_name']) in scrapped_pairs:
                print("Ignoring this Pair, already scrapped: ", sub_category['category_name'], sub_category['sub_category_name'])
            if (sub_category['category_name'], sub_category['sub_category_name']) not in scrapped_pairs:
                print("Getting jobs for :", sub_category['category_name'], sub_category['sub_category_name'])
                get_jobs_info(web_driver, sub_category, jobs_info)
                if jobs_info:
                    jobs.append(jobs_info)
                    write_to_csv(jobs_info, ['category_name','sub_category_name','title', 'URL', 'company', 'salary', 'experience', 'other_info', 'description'])

    '''
    web_driver.quit()
