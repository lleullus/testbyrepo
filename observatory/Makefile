.PHONY: test demo overview

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

demo:
	python3 examples/create_demo_projects.py .demo-projects
	PYTHONPATH=src python3 -m iis_observatory overview .demo-projects --no-color

overview:
	PYTHONPATH=src python3 -m iis_observatory overview $${HOME}/project --no-color
