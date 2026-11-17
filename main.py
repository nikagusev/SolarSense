from drafter import *
from dataclasses import dataclass
from bakery import assert_equal


@dataclass
class SolarSystem:
    """A named solar configuration and its household's daily demand."""
    name: str
    area: float
    sunlight_hours: float
    efficiency: float
    losses: float
    daily_usage: float


@dataclass
class State:
    """Information remembered while the visitor uses SolarSense."""
    current_system: SolarSystem
    generated_energy: float
    coverage_percentage: float
    saved_systems: list[SolarSystem]
    message: str
    calculated: bool


def initial_state() -> State:
    """Create a new session with example inputs and no saved systems."""
    return State(SolarSystem("My rooftop", 20.0, 5.0, 20.0, 15.0, 30.0),
                 0.0, 0.0, [], "", False)


def solar_energy(system: SolarSystem) -> float:
    """Estimate daily electricity in kWh at reference irradiance of 1 kW/m²."""
    return (system.area * system.sunlight_hours * system.efficiency / 100
            * (1 - system.losses / 100))


def coverage(energy: float, demand: float) -> float:
    """Return potential demand coverage, capped at 100 percent."""
    if demand <= 0:
        return 0.0
    return min(100.0, energy / demand * 100)


def remaining_energy(energy: float, demand: float) -> float:
    """Return the nonnegative daily energy shortfall in kWh."""
    if energy >= demand:
        return 0.0
    return demand - energy


def surplus_energy(energy: float, demand: float) -> float:
    """Return daily generation beyond daily household demand."""
    if energy <= demand:
        return 0.0
    return energy - demand


def validate(system: SolarSystem) -> str:
    """Return an explanation of the first invalid input, or an empty string."""
    if not system.name.strip():
        return "Please enter a system name."
    if not 0 < system.area <= 1000000:
        return "Panel area must be greater than zero and at most 1,000,000 m²."
    if not 0 <= system.sunlight_hours <= 24:
        return "Peak sunlight hours must be between 0 and 24."
    if not 0 < system.efficiency <= 100:
        return "Efficiency must be greater than 0 and at most 100%."
    if not 0 <= system.losses <= 100:
        return "System losses must be between 0 and 100%."
    if not 0 < system.daily_usage <= 1000000:
        return "Daily usage must be greater than zero and at most 1,000,000 kWh."
    return ""


def assessment(energy: float, demand: float) -> str:
    """Explain how estimated generation compares with household demand."""
    if round(energy - demand, 8) == 0:
        return "Your estimated solar generation matches your daily electricity needs."
    if energy > demand:
        return "Your estimated solar generation exceeds your daily electricity needs."
    return "Your solar panels could cover part of your daily electricity needs."


def navigation() -> list:
    """Create navigation links shared by the five pages."""
    return [Link("Home", "index"), " | ", Link("Calculator", "calculator"),
            " | ", Link("My Systems", "saved_systems"), " | ", Link("Learn", "learn"),
            HorizontalRule()]


@route
def index(state: State) -> Page:
    """Introduce SolarSense and link to its main features."""
    return Page(state, navigation() + [
        Header("SolarSense"),
        Header("A brighter, more sustainable future", 2),
        "Discover how solar energy could reduce your household's reliance on the grid.",
        Paragraph("Estimate daily generation, compare it with your electricity needs, "
                  "and save different solar configurations."),
        Button("Calculate your solar potential", "calculator"),
        Button("Explore saved systems", "saved_systems"),
        Button("Learn about solar energy", "learn")
    ])


@route
def calculator(state: State) -> Page:
    """Display the input form, with the current configuration as defaults."""
    system = state.current_system
    content = navigation() + [Header("Solar Calculator")]
    if state.message != "":
        content.append(Paragraph(state.message))
    content += [
        Paragraph("Enter your system details. The starting values are examples."),
        "System name", TextBox("name", system.name), LineBreak(),
        "Total solar panel area (m²)", TextBox("area", str(system.area)), LineBreak(),
        "Average peak sunlight hours per day", TextBox("hours", str(system.sunlight_hours)),
        LineBreak(), "Solar panel efficiency (%)", TextBox("efficiency", str(system.efficiency)),
        LineBreak(), "Estimated system losses (%)", TextBox("losses", str(system.losses)),
        LineBreak(), "Daily household electricity use (kWh)",
        TextBox("usage", str(system.daily_usage)), LineBreak(),
        Paragraph("Use peak sun hours, not total daylight hours. See Learn for an explanation."),
        Button("Calculate", "calculate")
    ]
    return Page(state, content)


@route
def calculate(state: State, name: str, area: str, hours: str,
              efficiency: str, losses: str, usage: str) -> Page:
    """Validate the form, update state, and show the estimated results."""
    # try/except handles invalid numeric text without crashing the website.
    # float() converts a text input into a decimal number; ValueError means
    # that the text was not a valid number.
    try:
        system = SolarSystem(name.strip(), float(area), float(hours),
                             float(efficiency), float(losses), float(usage))
    except ValueError:
        state.message = "Please enter numbers in all five numerical fields."
        return calculator(state)
    error = validate(system)
    if error != "":
        state.message = error
        return calculator(state)
    state.current_system = system
    state.generated_energy = solar_energy(system)
    state.coverage_percentage = coverage(state.generated_energy, system.daily_usage)
    state.calculated = True
    state.message = ""
    return results(state)


@route
def results(state: State) -> Page:
    """Display the latest valid calculation and a button to save it."""
    if not state.calculated:
        return Page(state, navigation() + [Header("Your Results"),
                    "Calculate a system first.", Button("Open calculator", "calculator")])
    system = state.current_system
    energy = state.generated_energy
    demand = system.daily_usage
    return Page(state, navigation() + [
        Header("Your Results"), Header(system.name, 2),
        Paragraph(f"Daily solar production: {energy:.2f} kWh"),
        Paragraph(f"Daily household demand: {demand:.2f} kWh"),
        Header(f"{state.coverage_percentage:.1f}% potential solar coverage", 2),
        ProgressBar(state.coverage_percentage, 100),
        Paragraph(f"Remaining daily energy need: {remaining_energy(energy, demand):.2f} kWh"),
        Paragraph(f"Excess daily solar generation: {surplus_energy(energy, demand):.2f} kWh"),
        Paragraph(assessment(energy, demand)),
        Paragraph("This compares daily energy totals. Actual grid imports depend on when "
                  "electricity is generated and used, and on storage or export arrangements."),
        Button("Save this system", "save_system"),
        Button("Change inputs", "calculator")
    ])


@route
def save_system(state: State) -> Page:
    """Save a copy of the current calculated solar configuration."""
    if not state.calculated:
        state.message = "Calculate a system before saving it."
        return saved_systems(state)
    system = state.current_system
    state.saved_systems.append(SolarSystem(system.name, system.area, system.sunlight_hours,
                                           system.efficiency, system.losses, system.daily_usage))
    state.message = "System saved."
    return saved_systems(state)


@route
def saved_systems(state: State) -> Page:
    """Display each saved system with comparable production and coverage."""
    content = navigation() + [Header("My Solar Systems"),
                              "Compare your saved configurations during this session."]
    if state.message != "":
        content.append(Paragraph(state.message))
    if len(state.saved_systems) == 0:
        content.append(Paragraph("No saved systems yet. Calculate and save one first."))
    position = 0
    for system in state.saved_systems:
        energy = solar_energy(system)
        percent = coverage(energy, system.daily_usage)
        content += [HorizontalRule(), Header(system.name, 2),
                    Paragraph(f"Area: {system.area} m² | Peak sun: {system.sunlight_hours} hours"),
                    Paragraph(f"Efficiency: {system.efficiency}% | Losses: {system.losses}%"),
                    Paragraph(f"Generation: {energy:.2f} kWh/day | Demand: {system.daily_usage:.2f} kWh/day"),
                    Paragraph(f"Potential coverage: {percent:.1f}%"), ProgressBar(percent, 100),
                    Paragraph(f"Remaining need: {remaining_energy(energy, system.daily_usage):.2f} kWh/day"),
                    Button("Delete this system", "delete_system", [("position", position)])]
        position += 1
    content += [HorizontalRule(), Button("Calculate another system", "calculator")]
    return Page(state, content)


@route
def delete_system(state: State, position: int) -> Page:
    """Delete the chosen saved system if its list position is valid."""
    if 0 <= position < len(state.saved_systems):
        state.saved_systems.pop(position)
        state.message = "System deleted."
    else:
        state.message = "That system could not be found."
    return saved_systems(state)


@route
def learn(state: State) -> Page:
    """Explain the inputs, equations and limitations of the calculator."""
    return Page(state, navigation() + [
        Header("Learn About Solar"),
        Header("How do solar panels work?", 2),
        Paragraph("Photovoltaic panels convert sunlight into electricity. An inverter "
                  "converts their direct current into alternating current for household use."),
        Header("What are peak sunlight hours?", 2),
        Paragraph("Peak sunlight hours are equivalent hours of sunlight at 1 kW/m², "
                  "not the total hours between sunrise and sunset."),
        Header("How is energy calculated?", 2),
        Paragraph("Daily kWh = area × peak sun hours × 1 kW/m² × efficiency × (1 − losses). "
                  "Efficiency and losses are converted from percentages to decimals."),
        Paragraph("Potential coverage = generation ÷ daily usage × 100, capped at 100%."),
        Header("Can I stop using the grid?", 2),
        Paragraph("Not necessarily. Solar panels do not generate electricity at night. "
                  "Daily energy totals cannot predict actual grid purchases or off-grid operation."),
        Paragraph("This is an educational estimate, not a professional installation forecast."),
        Button("Try the calculator", "calculator")
    ])


def run_tests() -> None:
    """Test calculation helpers, all eight routes, and common input errors."""
    system = SolarSystem("Test", 20.0, 5.0, 20.0, 15.0, 30.0)
    assert_equal(solar_energy(system), 17.0)
    assert_equal(solar_energy(SolarSystem("Dark", 20, 0, 20, 15, 30)), 0.0)
    assert_equal(round(coverage(17, 30), 2), 56.67)
    assert_equal(coverage(40, 30), 100.0)
    assert_equal(coverage(20, 0), 0.0)
    assert_equal(remaining_energy(17, 30), 13.0)
    assert_equal(remaining_energy(40, 30), 0.0)
    assert_equal(surplus_energy(40, 30), 10.0)
    assert_equal(surplus_energy(17, 30), 0.0)
    assert_equal(validate(system), "")
    assert_equal(validate(SolarSystem("Test", -1, 5, 20, 15, 30)) != "", True)
    assert_equal(validate(SolarSystem("Test", 20, 5, 101, 15, 30)) != "", True)
    assert_equal(validate(SolarSystem("Test", 20, 5, 20, 15, 0)) != "", True)
    assert_equal(validate(SolarSystem("Test", 20, float("nan"), 20, 15, 30)) != "", True)
    assert_equal(assessment(30, 30), "Your estimated solar generation matches your daily electricity needs.")
    assert_equal(assessment(31, 30), "Your estimated solar generation exceeds your daily electricity needs.")
    assert_equal(index(initial_state()).state, initial_state())
    assert_equal(calculator(initial_state()).state, initial_state())
    assert_equal(results(initial_state()).state.calculated, False)
    assert_equal(learn(initial_state()).state, initial_state())
    assert_equal(saved_systems(initial_state()).state.saved_systems, [])
    calculated = calculate(initial_state(), "Test", "20", "5", "20", "15", "30").state
    assert_equal(calculated.current_system, system)
    assert_equal(calculated.generated_energy, 17.0)
    assert_equal(round(calculated.coverage_percentage, 2), 56.67)
    assert_equal(results(calculated).state.calculated, True)
    assert_equal(calculate(initial_state(), "Test", "bad", "5", "20", "15", "30").state.message,
                 "Please enter numbers in all five numerical fields.")
    assert_equal(calculate(initial_state(), "Test", "20", "5", "20", "15", "0").state.calculated, False)
    assert_equal(save_system(initial_state()).state.saved_systems, [])
    assert_equal(save_system(calculated).state.saved_systems, [system])
    updated = calculate(calculated, "Second", "40", "5", "20", "15", "30").state
    assert_equal(save_system(updated).state.saved_systems[0], system)
    assert_equal(len(saved_systems(updated).state.saved_systems), 2)
    assert_equal(delete_system(updated, 0).state.saved_systems[0].name, "Second")
    assert_equal(len(delete_system(updated, 99).state.saved_systems), 1)
    assert_equal(delete_system(updated, 0).state.saved_systems, [])


set_website_title("SolarSense")
set_site_information(
    author="Nika Gusev",
    description="Estimate solar electricity production and potential reductions in grid dependence.",
    sources="Drafter documentation, PVWatts, PVGIS, and ChatGPT (AI-assisted development).",
    planning=["PLANNING.md"],
    links=["https://pvwatts.nlr.gov/pvwatts.php", "https://drafter-edu.github.io/drafter/"]
)
# CSS is optional presentation styling; it does not affect the Python calculations.
# Selectors choose HTML elements and the properties control their appearance.
add_website_css("h1", "color: #176447; font-weight: 700;")
add_website_css("h2", "color: #276749;")
add_website_css("button", "margin: 5px; border-radius: 8px;")
add_website_css("input", "margin: 6px 0 12px 0; max-width: 100%;")
add_website_css("progress", "width: 100%; accent-color: #25865b;")
run_tests()
start_server(initial_state())
