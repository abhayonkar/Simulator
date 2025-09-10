#!/usr/bin/env python
import os, sys
def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gas_sim.settings')
    try:
        from django.core.management import execute_from_command_line
    except Exception as exc:
        print('Django not installed or settings missing. This is a scaffold.')
        raise
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
