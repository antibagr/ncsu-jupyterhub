c = get_config()

c.CourseDirectory.course_id = "test_course"

c.Exchange.root = "/srv/nbgrader/exchange"

c.HubAuth.hub_base_url = "https://jhub-dev.cos.ncsu.edu:443"
c.HubAuth.hub_port = 443
