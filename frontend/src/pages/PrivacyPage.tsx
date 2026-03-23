import { useEffect } from 'react';
import { Link } from 'react-router-dom';

const LAST_UPDATED = 'March 22, 2026';

interface SectionProps {
  id: string;
  title: string;
  children: React.ReactNode;
}

function Section({ id, title, children }: SectionProps) {
  return (
    <section id={id} className="mb-10">
      <h2 className="text-xl font-semibold text-text-primary mb-4 pb-2 border-b border-border-light">
        {title}
      </h2>
      <div className="space-y-3 text-text-secondary leading-relaxed">{children}</div>
    </section>
  );
}

function SubSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mt-5">
      <h3 className="text-base font-semibold text-text-primary mb-2">{title}</h3>
      <div className="space-y-2 text-text-secondary leading-relaxed">{children}</div>
    </div>
  );
}

export default function PrivacyPage() {
  useEffect(() => {
    document.title = 'Privacy Policy | Interview Simulator — CodeSwiftr';
  }, []);

  return (
    <div className="min-h-screen bg-surface-primary py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-10">
          <p className="text-sm text-text-tertiary mb-2">Legal</p>
          <h1 className="text-3xl font-bold text-text-primary mb-3">Privacy Policy</h1>
          <p className="text-text-secondary text-sm">
            Last updated: <span className="font-medium text-text-primary">{LAST_UPDATED}</span>
          </p>
          <p className="mt-4 text-text-secondary">
            CodeSwiftr (&quot;we&quot;, &quot;our&quot;, &quot;us&quot;), operated by Bogdan Veliscu, is committed to
            protecting your personal data. This Privacy Policy explains what data we collect when you use{' '}
            <a
              href="https://app.codeswiftr.com"
              className="text-electric-blue hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              app.codeswiftr.com
            </a>{' '}
            (the &quot;Service&quot;), how we use it, and your rights under the General Data Protection Regulation
            (GDPR) and applicable EU law.
          </p>
          <p className="mt-3 text-text-secondary">
            By creating an account or using the Service, you acknowledge that you have read and understood this
            policy. If you do not agree, please do not use the Service.
          </p>
        </div>

        {/* Table of Contents */}
        <div className="bg-surface-secondary border border-border-light rounded-xl p-5 mb-10">
          <p className="text-sm font-semibold text-text-primary mb-3">Table of Contents</p>
          <ol className="space-y-1.5 text-sm text-electric-blue list-decimal list-inside">
            {[
              ['#who-we-are', 'Who We Are'],
              ['#data-we-collect', 'Data We Collect'],
              ['#how-we-use-data', 'How We Use Your Data'],
              ['#legal-basis', 'Legal Basis for Processing'],
              ['#third-parties', 'Third-Party Services'],
              ['#data-retention', 'Data Retention'],
              ['#international-transfers', 'International Data Transfers'],
              ['#your-rights', 'Your Rights (GDPR)'],
              ['#cookies', 'Cookies and Tracking'],
              ['#security', 'Security'],
              ['#children', 'Children\'s Privacy'],
              ['#changes', 'Changes to This Policy'],
              ['#contact', 'Contact Us'],
            ].map(([href, label]) => (
              <li key={href}>
                <a href={href} className="hover:underline">
                  {label}
                </a>
              </li>
            ))}
          </ol>
        </div>

        {/* Sections */}
        <Section id="who-we-are" title="1. Who We Are">
          <p>
            The data controller for the Interview Simulator service is:
          </p>
          <div className="bg-surface-secondary border border-border-light rounded-lg p-4 mt-3 text-sm font-mono text-text-primary space-y-0.5">
            <p>CodeSwiftr</p>
            <p>Operated by: Bogdan Veliscu</p>
            <p>Product: Interview Simulator</p>
            <p>
              Website:{' '}
              <a
                href="https://app.codeswiftr.com"
                className="text-electric-blue hover:underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                app.codeswiftr.com
              </a>
            </p>
            <p>
              Contact:{' '}
              <a href="mailto:support@codeswiftr.com" className="text-electric-blue hover:underline">
                support@codeswiftr.com
              </a>
            </p>
          </div>
          <p className="mt-3">
            As data controller, we are responsible for deciding how and why your personal data is processed.
          </p>
        </Section>

        <Section id="data-we-collect" title="2. Data We Collect">
          <p>We collect the following categories of personal data:</p>

          <SubSection title="2.1 Account Information">
            <p>
              When you register, we collect your <strong className="text-text-primary">full name</strong> and{' '}
              <strong className="text-text-primary">email address</strong>. This data is necessary to create
              and manage your account.
            </p>
          </SubSection>

          <SubSection title="2.2 Audio Recordings">
            <p>
              During interview practice sessions, you may record audio answers to interview questions. These{' '}
              <strong className="text-text-primary">audio recordings</strong> are uploaded to our secure
              servers for transcription and AI-powered feedback analysis. Recordings are processed by
              OpenAI's Whisper API for speech-to-text conversion.
            </p>
            <p>
              Audio files are stored temporarily for processing and then retained as part of your session
              history. You may delete individual sessions at any time from your account settings.
            </p>
          </SubSection>

          <SubSection title="2.3 AI-Generated Feedback">
            <p>
              Transcriptions of your answers are processed by Anthropic's Claude AI to generate structured
              feedback, including scores, strengths, and improvement suggestions. This{' '}
              <strong className="text-text-primary">AI-generated feedback</strong> is stored alongside your
              session data and is only accessible to you.
            </p>
          </SubSection>

          <SubSection title="2.4 Payment Information">
            <p>
              Payment processing is handled entirely by{' '}
              <strong className="text-text-primary">Stripe</strong>. We do not store your credit card
              numbers, CVV codes, or full payment details on our servers. We receive and store only:
            </p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>Your Stripe customer ID</li>
              <li>Subscription status (free, pro, or team)</li>
              <li>Billing period and renewal dates</li>
            </ul>
          </SubSection>

          <SubSection title="2.5 Usage and Analytics Data">
            <p>
              We collect anonymized usage data through PostHog to understand how users interact with the
              product. This may include page views, feature usage, session duration, and click events.
              PostHog analytics are configured to respect Do Not Track signals and are processed under a
              data processing agreement.
            </p>
          </SubSection>

          <SubSection title="2.6 Technical Data">
            <p>
              We automatically collect certain technical information when you access the Service, including
              your IP address (for security and rate limiting), browser type, operating system, and
              referral URLs. This data is used to maintain security and improve service reliability.
            </p>
          </SubSection>
        </Section>

        <Section id="how-we-use-data" title="3. How We Use Your Data">
          <p>We process your personal data for the following purposes:</p>
          <ul className="list-disc list-inside space-y-2 ml-2">
            <li>
              <strong className="text-text-primary">Account management</strong> — creating, authenticating,
              and maintaining your account
            </li>
            <li>
              <strong className="text-text-primary">Interview processing</strong> — transcribing your audio
              responses and generating AI feedback
            </li>
            <li>
              <strong className="text-text-primary">Subscription billing</strong> — managing your
              subscription through Stripe, processing payments, and sending billing notifications
            </li>
            <li>
              <strong className="text-text-primary">Service communications</strong> — sending transactional
              emails (account confirmation, password reset, billing receipts)
            </li>
            <li>
              <strong className="text-text-primary">Product improvement</strong> — analyzing aggregated,
              anonymized usage patterns to improve the Service
            </li>
            <li>
              <strong className="text-text-primary">Security and fraud prevention</strong> — monitoring for
              abuse, rate limiting, and protecting user accounts
            </li>
            <li>
              <strong className="text-text-primary">Legal compliance</strong> — meeting our obligations
              under applicable law, including tax and accounting requirements
            </li>
          </ul>
          <p className="mt-3">
            We do not sell your personal data. We do not use your interview recordings or AI-generated
            feedback to train AI models without explicit, separate consent.
          </p>
        </Section>

        <Section id="legal-basis" title="4. Legal Basis for Processing">
          <p>
            Under the GDPR, we process your personal data on the following legal bases:
          </p>
          <div className="overflow-x-auto mt-3">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-surface-secondary">
                  <th className="text-left p-3 border border-border-light text-text-primary font-semibold rounded-tl-lg">
                    Processing Activity
                  </th>
                  <th className="text-left p-3 border border-border-light text-text-primary font-semibold rounded-tr-lg">
                    Legal Basis
                  </th>
                </tr>
              </thead>
              <tbody>
                {[
                  ['Account creation and management', 'Contract (Art. 6(1)(b) GDPR)'],
                  ['Interview transcription and AI feedback', 'Contract (Art. 6(1)(b) GDPR)'],
                  ['Payment processing via Stripe', 'Contract (Art. 6(1)(b) GDPR)'],
                  ['Transactional emails', 'Contract (Art. 6(1)(b) GDPR)'],
                  ['Analytics (PostHog)', 'Legitimate interest (Art. 6(1)(f) GDPR)'],
                  ['Security monitoring', 'Legitimate interest (Art. 6(1)(f) GDPR)'],
                  ['Legal and tax obligations', 'Legal obligation (Art. 6(1)(c) GDPR)'],
                ].map(([activity, basis], i) => (
                  <tr key={i} className="hover:bg-surface-secondary/50 transition-colors">
                    <td className="p-3 border border-border-light text-text-secondary">{activity}</td>
                    <td className="p-3 border border-border-light text-text-secondary">{basis}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        <Section id="third-parties" title="5. Third-Party Services">
          <p>
            We share your data only with the third-party processors necessary to deliver the Service. Each
            is bound by a Data Processing Agreement (DPA) and appropriate safeguards.
          </p>

          <SubSection title="5.1 Stripe (Payment Processing)">
            <p>
              Stripe, Inc. processes payments on our behalf. Your payment card details go directly to
              Stripe and are never transmitted to our servers. Stripe is PCI-DSS Level 1 certified.
              Privacy Policy:{' '}
              <a
                href="https://stripe.com/privacy"
                className="text-electric-blue hover:underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                stripe.com/privacy
              </a>
            </p>
          </SubSection>

          <SubSection title="5.2 OpenAI (Audio Transcription)">
            <p>
              Your audio recordings are sent to OpenAI's Whisper API for speech-to-text transcription.
              OpenAI does not use API inputs to train its models by default. Data sent via the API is
              retained by OpenAI for up to 30 days for safety monitoring. Privacy Policy:{' '}
              <a
                href="https://openai.com/privacy"
                className="text-electric-blue hover:underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                openai.com/privacy
              </a>
            </p>
          </SubSection>

          <SubSection title="5.3 Anthropic (AI Feedback Generation)">
            <p>
              Transcribed text from your interview answers is sent to Anthropic's Claude API to generate
              structured feedback. Anthropic does not use API inputs to train its models. Data is retained
              by Anthropic for up to 30 days. Privacy Policy:{' '}
              <a
                href="https://www.anthropic.com/privacy"
                className="text-electric-blue hover:underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                anthropic.com/privacy
              </a>
            </p>
          </SubSection>

          <SubSection title="5.4 PostHog (Analytics)">
            <p>
              PostHog collects anonymized usage analytics. We self-host PostHog or use PostHog Cloud with
              data processed under a DPA. PostHog may set cookies on your browser. You can opt out via
              your browser's privacy settings or by contacting us. Privacy Policy:{' '}
              <a
                href="https://posthog.com/privacy"
                className="text-electric-blue hover:underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                posthog.com/privacy
              </a>
            </p>
          </SubSection>

          <SubSection title="5.5 Railway (Hosting and Database)">
            <p>
              Our backend and PostgreSQL database are hosted on Railway. Your data is stored on Railway's
              infrastructure, which is located in the United States. Appropriate safeguards (Standard
              Contractual Clauses) are in place for transfers of EU personal data to Railway. Privacy
              Policy:{' '}
              <a
                href="https://railway.app/legal/privacy"
                className="text-electric-blue hover:underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                railway.app/legal/privacy
              </a>
            </p>
          </SubSection>

          <p className="mt-4">
            We do not share your personal data with any other third parties for marketing or advertising
            purposes.
          </p>
        </Section>

        <Section id="data-retention" title="6. Data Retention">
          <p>
            We retain your personal data only for as long as necessary for the purposes described in this
            policy.
          </p>
          <ul className="list-disc list-inside space-y-2 ml-2 mt-2">
            <li>
              <strong className="text-text-primary">Account data (name, email):</strong> Retained for as
              long as your account is active. Deleted within 30 days of account deletion request.
            </li>
            <li>
              <strong className="text-text-primary">Audio recordings:</strong> Retained as part of your
              session history. You can delete individual sessions at any time. Deleted within 30 days of
              account deletion.
            </li>
            <li>
              <strong className="text-text-primary">AI feedback and transcriptions:</strong> Retained with
              your session data. Deleted upon session or account deletion.
            </li>
            <li>
              <strong className="text-text-primary">Billing records:</strong> Retained for 7 years to
              meet EU tax and accounting obligations, even after account deletion.
            </li>
            <li>
              <strong className="text-text-primary">Analytics data:</strong> Retained in anonymized,
              aggregated form indefinitely. Identifiable analytics events are deleted with your account.
            </li>
          </ul>
        </Section>

        <Section id="international-transfers" title="7. International Data Transfers">
          <p>
            Some of our third-party processors (including OpenAI, Anthropic, Railway, and Stripe) are
            based in the United States. When we transfer your personal data outside the European Economic
            Area (EEA), we ensure that appropriate safeguards are in place, such as:
          </p>
          <ul className="list-disc list-inside space-y-1.5 ml-2 mt-2">
            <li>Standard Contractual Clauses (SCCs) approved by the European Commission</li>
            <li>Data Processing Agreements with each processor</li>
            <li>
              Adequacy decisions where applicable (the EU-US Data Privacy Framework where the processor
              is certified)
            </li>
          </ul>
          <p className="mt-3">
            You may request a copy of the relevant safeguards by contacting us at{' '}
            <a href="mailto:support@codeswiftr.com" className="text-electric-blue hover:underline">
              support@codeswiftr.com
            </a>
            .
          </p>
        </Section>

        <Section id="your-rights" title="8. Your Rights (GDPR)">
          <p>
            As a data subject under the GDPR, you have the following rights. To exercise any of these
            rights, email{' '}
            <a href="mailto:support@codeswiftr.com" className="text-electric-blue hover:underline">
              support@codeswiftr.com
            </a>
            . We will respond within 30 days.
          </p>
          <ul className="list-disc list-inside space-y-2 ml-2 mt-3">
            <li>
              <strong className="text-text-primary">Right of access</strong> — You may request a copy of
              all personal data we hold about you.
            </li>
            <li>
              <strong className="text-text-primary">Right to rectification</strong> — You may ask us to
              correct inaccurate or incomplete data.
            </li>
            <li>
              <strong className="text-text-primary">Right to erasure</strong> — You may request deletion
              of your personal data. You can also delete your account directly from Settings.
            </li>
            <li>
              <strong className="text-text-primary">Right to restriction</strong> — You may ask us to
              restrict processing of your data in certain circumstances.
            </li>
            <li>
              <strong className="text-text-primary">Right to data portability</strong> — You may request
              your data in a structured, machine-readable format (JSON).
            </li>
            <li>
              <strong className="text-text-primary">Right to object</strong> — You may object to
              processing based on our legitimate interests (e.g., analytics).
            </li>
            <li>
              <strong className="text-text-primary">Rights related to automated decision-making</strong>{' '}
              — AI-generated feedback scores are informational only and do not constitute automated
              decisions with legal or significant effects.
            </li>
          </ul>
          <p className="mt-4">
            If you believe we have not handled your data lawfully, you have the right to lodge a
            complaint with your national data protection supervisory authority within the EU.
          </p>
        </Section>

        <Section id="cookies" title="9. Cookies and Tracking">
          <p>We use the following cookies and tracking technologies:</p>
          <ul className="list-disc list-inside space-y-2 ml-2 mt-2">
            <li>
              <strong className="text-text-primary">Authentication cookies</strong> — Session tokens
              stored in HTTP-only cookies or localStorage, necessary for you to stay logged in. These are
              strictly necessary and cannot be disabled.
            </li>
            <li>
              <strong className="text-text-primary">Analytics cookies (PostHog)</strong> — Used to
              collect anonymized usage statistics. You can opt out by contacting us or configuring your
              browser to block third-party cookies.
            </li>
          </ul>
          <p className="mt-3">
            We do not use advertising cookies or tracking pixels. We do not participate in cross-site
            advertising networks.
          </p>
        </Section>

        <Section id="security" title="10. Security">
          <p>
            We implement appropriate technical and organizational measures to protect your personal data
            against unauthorized access, disclosure, alteration, or destruction:
          </p>
          <ul className="list-disc list-inside space-y-1.5 ml-2 mt-2">
            <li>All data in transit is encrypted using TLS 1.2 or higher</li>
            <li>Passwords are hashed using industry-standard algorithms (bcrypt)</li>
            <li>Authentication tokens are short-lived and rotated on refresh</li>
            <li>Database access is restricted by network-level controls on Railway</li>
            <li>API endpoints are rate-limited to prevent brute-force attacks</li>
          </ul>
          <p className="mt-3">
            In the event of a personal data breach that is likely to result in a risk to your rights and
            freedoms, we will notify the relevant supervisory authority within 72 hours and affected users
            without undue delay.
          </p>
        </Section>

        <Section id="children" title="11. Children's Privacy">
          <p>
            The Service is not directed at children under the age of 16. We do not knowingly collect
            personal data from children. If you believe we have inadvertently collected data from a child
            under 16, please contact us at{' '}
            <a href="mailto:support@codeswiftr.com" className="text-electric-blue hover:underline">
              support@codeswiftr.com
            </a>{' '}
            and we will delete it promptly.
          </p>
        </Section>

        <Section id="changes" title="12. Changes to This Policy">
          <p>
            We may update this Privacy Policy from time to time. When we make material changes, we will
            notify you by email or by displaying a notice in the application at least 14 days before the
            changes take effect.
          </p>
          <p>
            Continued use of the Service after the effective date of any changes constitutes your
            acceptance of the revised policy. The &quot;Last updated&quot; date at the top of this page
            reflects the most recent revision.
          </p>
        </Section>

        <Section id="contact" title="13. Contact Us">
          <p>
            If you have any questions about this Privacy Policy or how we handle your data, please
            contact us:
          </p>
          <div className="bg-surface-secondary border border-border-light rounded-lg p-4 mt-3 text-sm space-y-1">
            <p className="text-text-primary font-medium">CodeSwiftr — Data Enquiries</p>
            <p>
              Email:{' '}
              <a href="mailto:support@codeswiftr.com" className="text-electric-blue hover:underline">
                support@codeswiftr.com
              </a>
            </p>
            <p>
              Subject line: <span className="text-text-primary">Privacy Request — [your name]</span>
            </p>
          </div>
          <p className="mt-4">
            You also have the right to lodge a complaint with the data protection supervisory authority
            in your EU member state.
          </p>
        </Section>

        {/* Footer nav */}
        <div className="mt-12 pt-6 border-t border-border-light flex flex-wrap gap-4 text-sm text-text-tertiary">
          <Link to="/" className="hover:text-electric-blue transition-colors">
            Home
          </Link>
          <Link to="/terms" className="hover:text-electric-blue transition-colors">
            Terms of Service
          </Link>
          <a href="mailto:support@codeswiftr.com" className="hover:text-electric-blue transition-colors">
            Contact
          </a>
        </div>
      </div>
    </div>
  );
}
