name: die_another_day
slug: die_another_day
film: "Die Another Day (2002)"
codename: ICARUS
package_root: "."
identity:
  title: "Die Another Day: ICARUS — Special-Agent Mission Software"
  description: "PROJECT BOND film package: biometric identity-replacement detection, ice-palace cold-environment operations planning, and orbital-mirror targeting, behind a frozen BOND-API MissionProvider adapter."
  concepts:
    - identity_detection
    - ice_ops
    - orbital_mirror
protocol:
  provider_module: "die_another_day.mission"
  provider_class: "MissionProvider"
  film: "die_another_day"
  gadgets: ["identity_detection", "ice_ops", "orbital_mirror"]
