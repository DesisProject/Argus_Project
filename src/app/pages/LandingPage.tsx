import { useNavigate } from "react-router";
import { Button } from "../components/ui/button";
import {
  TrendingUp,
  Layers,
  GitCompare,
  Shield,
  BarChart3,
  Check,
  ChevronRight,
} from "lucide-react";
import { Card, CardContent } from "../components/ui/card";
import image1 from "../assets/image1.png";
import image2 from "../assets/image2.png";
import image3 from "../assets/image3.png";
import image4 from "../assets/image4.png";

export function LandingPage() {
  const navigate = useNavigate();

  const features = [
    {
      icon: BarChart3,
      title: "Financial Modeling Dashboard",
      description:
        "Model your baseline cash position with revenue growth, costs, and burn rate projections over 24 months.",
    },
    {
      icon: Layers,
      title: "Scenario Builder with Lag, Ramp & Duration",
      description:
        "Define decisions and events with realistic timing parameters including lag effects and gradual ramp periods.",
    },
    {
      icon: GitCompare,
      title: "Uncertainty Comparison (Best / Expected / Worst)",
      description:
        "Visualize multiple scenarios simultaneously and understand the range of possible outcomes.",
    },
    {
      icon: Shield,
      title: "Automated Mitigation Suggestions",
      description:
        "Get intelligent recommendations on risk factors and actions to improve financial resilience.",
    },
  ];

  const walkthrough = [
    {
      step: 1,
      title: "Define Financial Baseline",
      description: "Input your starting cash, revenue, costs, and growth assumptions.",
      image: image1,
    },
    {
      step: 2,
      title: "Add Business Decisions",
      description: "Layer in hiring, marketing, expansion, or other strategic moves.",
      image: image2,
    },
    {
      step: 3,
      title: "Compare Outcomes Under Uncertainty",
      description: "See how different scenarios affect your runway and cash position.",
      image: image3,
    },
    {
      step: 4,
      title: "View Risk Metrics & Mitigation",
      description: "Get resilience grades, insolvency risk, and actionable recommendations.",
      image: image4,
    },
  ];

  const testimonials = [
    {
      name: "Sarah Chen",
      title: "CEO, Momentum Labs",
      quote:
        "Argus helped us visualize the impact of our hiring plan before committing. We adjusted our timeline and saved 4 months of runway.",
      avatar: "https://images.unsplash.com/photo-1610631066894-62452ccb927c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwcm9mZXNzaW9uYWwlMjBmZW1hbGUlMjBDRU8lMjBidXNpbmVzcyUyMHBvcnRyYWl0fGVufDF8fHx8MTc3MjQzOTQ1M3ww&ixlib=rb-4.1.0&q=80&w=200",
    },
    {
      name: "Marcus Johnson",
      title: "Founder, Velocity Finance",
      quote:
        "The scenario builder is brilliant. We can model complex decisions with realistic lag and ramp effects. It's changed how we plan.",
      avatar: "https://images.unsplash.com/photo-1659353220869-69b81aa34051?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwcm9mZXNzaW9uYWwlMjBtYWxlJTIwZm91bmRlciUyMGVudHJlcHJlbmV1ciUyMHBvcnRyYWl0fGVufDF8fHx8MTc3MjQzOTQ1M3ww&ixlib=rb-4.1.0&q=80&w=200",
    },
    {
      name: "David Park",
      title: "CFO, NexGen Systems",
      quote:
        "Finally, a tool that lets us stress-test decisions before board meetings. The comparison view makes uncertainty tangible.",
      avatar: "https://images.unsplash.com/photo-1701463387028-3947648f1337?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwcm9mZXNzaW9uYWwlMjBhc2lhbiUyMENGTyUyMGJ1c2luZXNzJTIwcG9ydHJhaXR8ZW58MXx8fHwxNzcyNDM5NDUzfDA&ixlib=rb-4.1.0&q=80&w=200",
    },
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-slate-900/95 backdrop-blur-sm border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-teal-400 to-blue-500 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-semibold text-white">Argus</span>
            </div>

            <div className="flex items-center gap-8">
              <a href="#features" className="text-slate-300 hover:text-white transition-colors">
                Features
              </a>
              <a href="#product" className="text-slate-300 hover:text-white transition-colors">
                Product
              </a>
              {/* <a href="#pricing" className="text-slate-300 hover:text-white transition-colors">
                Pricing
              </a> */}
              <Button
                variant="ghost"
                onClick={() => navigate('/login')}
                className="text-slate-300 hover:text-white hover:bg-slate-800"
              >
                Sign In
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 overflow-hidden pt-20">
        {/* Background Effects */}
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-20 left-10 w-96 h-96 bg-teal-500/20 rounded-full blur-3xl" />
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-7xl mx-auto px-6 py-20">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center min-h-[calc(100vh-200px)]">
            {/* Left Side - Mockup */}
            <div className="relative">
              <div className="relative transform -rotate-6 transition-transform hover:rotate-0 duration-500">
                <div className="bg-white rounded-2xl shadow-2xl p-6 border border-slate-200">
                  {/* Mini Dashboard Preview */}
                  <div className="space-y-4">
                    {/* KPI Cards */}
                    <div className="grid grid-cols-3 gap-3">
                      <div className="bg-slate-50 rounded-lg p-3">
                        <div className="text-xs text-slate-600">Current Cash</div>
                        <div className="text-lg font-semibold text-slate-900">$500K</div>
                      </div>
                      <div className="bg-slate-50 rounded-lg p-3">
                        <div className="text-xs text-slate-600">Burn Rate</div>
                        <div className="text-lg font-semibold text-slate-900">$35K</div>
                      </div>
                      <div className="bg-green-50 rounded-lg p-3 border-2 border-green-200">
                        <div className="text-xs text-green-700">Runway</div>
                        <div className="text-lg font-semibold text-green-700">14mo</div>
                      </div>
                    </div>

                    {/* Chart Area */}
                    <div className="bg-slate-50 rounded-lg p-4 h-40">
                      <div className="flex items-end justify-between h-full">
                        {Array.from({ length: 12 }).map((_, i) => (
                          <div
                            key={i}
                            className="bg-gradient-to-t from-blue-500 to-blue-400 rounded-t w-6"
                            style={{ height: `${30 + Math.random() * 70}%` }}
                          />
                        ))}
                      </div>
                    </div>

                    {/* Scenario Pills */}
                    <div className="flex gap-2">
                      <div className="flex-1 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 text-xs text-blue-700">
                        Best Case
                      </div>
                      <div className="flex-1 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-700">
                        Expected
                      </div>
                      <div className="flex-1 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-xs text-red-700">
                        Worst Case
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Side - Content */}
            <div className="text-white space-y-8">
              <div className="space-y-4">
                <h1 className="text-5xl lg:text-6xl font-bold leading-tight">
                  Model Decisions.
                  <br />
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-blue-400">
                    See Risk.
                  </span>
                  <br />
                  Save Runway.
                </h1>
                <p className="text-xl text-slate-300 leading-relaxed">
                  Simulate strategic decisions, compare uncertainty scenarios, and evaluate your startup's financial survival with confidence.
                </p>
              </div>

              <div className="flex items-center gap-4">
                <Button
                  onClick={() => navigate('/signup')}
                  className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white px-8 py-6 text-lg rounded-full shadow-lg"
                >
                  Create Account
                  <ChevronRight className="w-5 h-5 ml-2" />
                </Button>
                <Button
                  onClick={() => navigate('/login')}
                  variant="ghost"
                  className="text-slate-300 hover:text-white hover:bg-slate-800 px-8 py-6 text-lg rounded-full"
                >
                  Sign In
                </Button>
              </div>

              {/* <div className="flex items-center gap-8 pt-4 text-sm text-slate-400">
                <div className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-teal-400" />
                  <span>No credit card required</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-teal-400" />
                  <span>14-day free trial</span>
                </div>
              </div> */}
            </div>
          </div>
        </div>

        {/* Wave Transition */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg
            viewBox="0 0 1440 120"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="w-full"
          >
            <path
              d="M0 0L60 10C120 20 240 40 360 46.7C480 53 600 47 720 43.3C840 40 960 40 1080 46.7C1200 53 1320 67 1380 73.3L1440 80V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0V0Z"
              fill="white"
            />
          </svg>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              Built for Decision Makers
            </h2>
            <p className="text-xl text-slate-600">
              Everything you need to model risk and optimize your runway
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <Card
                  key={index}
                  className="border border-slate-200 hover:border-blue-300 hover:shadow-lg transition-all duration-300 cursor-pointer group"
                >
                  <CardContent className="pt-6 space-y-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-teal-50 to-blue-50 flex items-center justify-center group-hover:scale-110 transition-transform">
                      <Icon className="w-6 h-6 text-blue-600" />
                    </div>
                    <h3 className="text-lg font-semibold text-slate-900">
                      {feature.title}
                    </h3>
                    <p className="text-slate-600 leading-relaxed">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Product Walkthrough */}
      <section id="product" className="py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-slate-600">
              From baseline to insights in four simple steps
            </p>
          </div>

          <div className="space-y-24"> {/* Increased spacing for better visual flow */}
            {walkthrough.map((item, index) => (
              <div
                key={index}
                className={`flex items-center gap-12 ${index % 2 === 1 ? "flex-row-reverse" : ""
                  }`}
              >
                <div className="flex-1">
                  <div className="inline-block px-4 py-2 bg-blue-100 text-blue-700 rounded-full font-semibold text-sm mb-4">
                    Step {item.step}
                  </div>
                  <h3 className="text-3xl font-bold text-slate-900 mb-4">
                    {item.title}
                  </h3>
                  <p className="text-lg text-slate-600 leading-relaxed">
                    {item.description}
                  </p>
                </div>

                <div className="flex-1">
                  <div className="bg-white rounded-2xl shadow-2xl overflow-hidden border border-slate-200 transition-transform hover:scale-[1.02]">
                    <img
                      src={item.image}
                      alt={`${item.title} Screenshot`}
                      className="w-full h-auto object-contain block"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              Trusted by Founders & CFOs
            </h2>
            <p className="text-xl text-slate-600">
              See how teams use Argus to make better decisions
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="border border-slate-200 shadow-sm">
                <CardContent className="pt-6 space-y-4">
                  <p className="text-slate-700 leading-relaxed italic">
                    "{testimonial.quote}"
                  </p>
                  <div className="flex items-center gap-4 pt-4 border-t border-slate-100">
                    <img
                      src={testimonial.avatar}
                      alt={testimonial.name}
                      className="w-12 h-12 rounded-full object-cover"
                    />
                    <div>
                      <div className="font-semibold text-slate-900">
                        {testimonial.name}
                      </div>
                      <div className="text-sm text-slate-600">
                        {testimonial.title}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-br from-slate-900 to-slate-800">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-4xl font-bold text-white mb-6">
            Ready to make smarter decisions?
          </h2>
          <p className="text-xl text-slate-300 mb-8">
            Join hundreds of founders using Argus to model risk and optimize runway.
          </p>
          <Button
            onClick={() => navigate('/signup')}
            className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white px-8 py-6 text-lg rounded-full shadow-lg"
          >
            Start
            <ChevronRight className="w-5 h-5 ml-2" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-teal-400 to-blue-500 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-semibold text-white">Argus</span>
            </div>
            <div className="text-slate-400 text-sm">
              © 2026 Argus. Risk-Aware Decision & Event Impact Simulator.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
